import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

import torch
from torch import nn
from torch_geometric.nn import RGCNConv


ROOT_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT_DIR / "model"
CHECKPOINT_PATH = MODEL_DIR / "checkpoints" / "best_model.pt"
FEATURE_STATS_PATH = MODEL_DIR / "processed_data" / "feature_stats.json"
FAST_STATS_PATH = MODEL_DIR / "processed_data" / "fast_stats.json"
TEXT_MODEL = "vinai/bertweet-base"
MAX_LEN = 50


def safe_div(numerator: float, denominator: float) -> float:
    if denominator in (0, 0.0):
        return 0.0
    return float(numerator) / float(denominator)


def entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    total = len(text)
    score = 0.0
    for count in counts.values():
        probability = count / total
        score -= probability * math.log(probability, 2)
    return score


def lev_distance(left: str, right: str) -> int:
    if left is None:
        left = ""
    if right is None:
        right = ""
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            if left_char == right_char:
                current.append(previous[j - 1])
            else:
                current.append(1 + min(previous[j - 1], previous[j], current[-1]))
        previous = current
    return previous[-1]


def normalize_for_bertweet(text: str) -> str:
    text = re.sub(r"@\w+", "@USER", text)
    text = re.sub(r"http\S+", "HTTPURL", text)
    return text


def mean_pool(hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).float()
    return (hidden_states * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)


class TMTM(nn.Module):
    def __init__(self, hidden_dimension=128, out_dim=2, relation_num=2, dropout=0.3):
        super().__init__()
        self.dropout = dropout
        branch_dim = int(hidden_dimension / 4)

        self.linear_relu_des = nn.Sequential(
            nn.Linear(768, branch_dim),
            nn.LeakyReLU(),
        )
        self.linear_relu_tweet = nn.Sequential(
            nn.Linear(768, branch_dim),
            nn.LeakyReLU(),
        )
        self.linear_relu_num_prop = nn.Sequential(
            nn.Linear(41, branch_dim),
            nn.LeakyReLU(),
        )
        self.linear_relu_cat_prop = nn.Sequential(
            nn.Linear(12, branch_dim),
            nn.LeakyReLU(),
        )

        self.linear_relu_input = nn.Sequential(
            nn.Linear(hidden_dimension, hidden_dimension),
            nn.LeakyReLU(),
        )

        self.rgcn1 = RGCNConv(hidden_dimension, hidden_dimension, num_relations=relation_num)
        self.rgcn2 = RGCNConv(hidden_dimension, hidden_dimension, num_relations=relation_num)

        self.layer_norm1 = nn.LayerNorm(hidden_dimension)
        self.layer_norm2 = nn.LayerNorm(hidden_dimension)

        self.linear_relu_output1 = nn.Sequential(
            nn.Linear(hidden_dimension, hidden_dimension),
            nn.LeakyReLU(),
        )
        self.linear_output2 = nn.Linear(hidden_dimension, out_dim)

    def forward(self, feature, edge_index, edge_type):
        d = self.linear_relu_des(feature[:, -1536:-768].to(torch.float32))
        t = self.linear_relu_tweet(feature[:, -768:].to(torch.float32))
        num = self.linear_relu_num_prop(feature[:, 12:53].to(torch.float32))
        cat = self.linear_relu_cat_prop(feature[:, 0:12].to(torch.float32))

        x = torch.cat((d, t, num, cat), dim=1)
        x = self.linear_relu_input(x)

        residual = x
        x = self.rgcn1(x, edge_index, edge_type)
        x = self.layer_norm1(x + residual)
        x = torch.nn.functional.dropout(x, p=self.dropout, training=self.training)

        residual = x
        x = self.rgcn2(x, edge_index, edge_type)
        x = self.layer_norm2(x + residual)
        x = torch.nn.functional.dropout(x, p=self.dropout, training=self.training)

        x = self.linear_relu_output1(x)
        x = self.linear_output2(x)
        return x


@dataclass
class PredictionResult:
    label: str
    confidence: float
    bot_probability: float
    human_probability: float
    signals: List[str]


class BotPredictor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        with open(FEATURE_STATS_PATH, "r", encoding="utf-8") as f:
            self.feature_stats = json.load(f)

        self.fast_stats = {}
        if FAST_STATS_PATH.exists():
            with open(FAST_STATS_PATH, "r", encoding="utf-8") as f:
                self.fast_stats = json.load(f)

        # Lazy import heavy NLP stack so backend boot is not blocked on startup.
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL)
        self.text_model = AutoModel.from_pretrained(TEXT_MODEL).to(self.device)
        self.text_model.eval()

        checkpoint = torch.load(CHECKPOINT_PATH, map_location=self.device)
        hidden_dimension = checkpoint.get("hidden_dimension", 128)
        dropout = checkpoint.get("dropout", 0.3)

        self.model = TMTM(hidden_dimension=hidden_dimension, out_dim=2, relation_num=2, dropout=dropout).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        self.reference_date = torch.tensor([2024.0, 2.0, 14.0])

    def _scale_counts(self, value: float, key: str, fallback_mean: float = 0.0, fallback_std: float = 1.0) -> float:
        stats = self.fast_stats.get(key)
        if stats:
            mean = float(stats.get("mean", fallback_mean))
            std = float(stats.get("std", fallback_std)) or 1.0
            return (float(value) - mean) / std
        return math.log1p(max(float(value), 0.0))

    def _mean_pool_texts(self, texts: List[str]) -> torch.Tensor:
        valid_texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not valid_texts:
            return torch.zeros((768,), dtype=torch.float32)

        normalized_texts = [normalize_for_bertweet(text) for text in valid_texts]
        inputs = self.tokenizer(
            normalized_texts,
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.inference_mode():
            hidden_states = self.text_model(**inputs).last_hidden_state
            pooled = mean_pool(hidden_states, inputs["attention_mask"])
        return pooled.mean(dim=0).cpu()

    def _vectorize(self, payload) -> torch.Tensor:
        username = (payload.username or "").strip()
        display_name = (payload.display_name or username).strip() or username
        description = (payload.description or "").strip()
        tweets = [tweet.strip() for tweet in (payload.sample_tweets or []) if isinstance(tweet, str) and tweet.strip()]

        followers = max(int(payload.followers_count or 0), 0)
        following = max(int(payload.following_count or 0), 0)
        tweet_count = max(int(payload.tweet_count or 0), 0)
        listed = max(int(payload.listed_count or 0), 0)

        active_days = max(1, (2024 - int(payload.created_year or 2024)) * 365)

        username_lower = username.lower()
        name_lower = display_name.lower()
        desc_lower = description.lower()

        cat = [
            int(bool(payload.protected)),
            int(bool(payload.verified)),
            int(bool(payload.default_profile_image)),
            int(bool(payload.has_location)),
            int(bool(payload.has_url)),
            int(bool(description)),
            int(bool(payload.has_pinned_tweet)),
            int("bot" in name_lower),
            int("bot" in username_lower),
            int("bot" in desc_lower),
            int((not description) and (not payload.has_location) and (not payload.has_url)),
            int(2 * followers >= 100),
        ]

        has_description = 1 if description else 0
        has_location = 1 if payload.has_location else 0
        has_url = 1 if payload.has_url else 0
        default_profile = 1 if payload.default_profile_image else 0

        hashtags_desc = len(re.findall(r"#\w+", description))
        urls_desc = len(re.findall(r"http[s]?://\S+", description))
        number_count_username = len(re.findall(r"\d+", username))
        number_count_name = len(re.findall(r"\d+", display_name))
        digits_username = sum(char.isdigit() for char in username)
        digits_name = sum(char.isdigit() for char in display_name)

        big_username = sum(char.isupper() for char in username)
        small_username = sum(char.islower() for char in username)
        big_name = sum(char.isupper() for char in display_name)
        small_name = sum(char.islower() for char in display_name)

        rel_upper_lower_username = safe_div(big_username, small_username) if small_username else 0.0
        rel_upper_lower_name = safe_div(big_name, small_name) if small_name else 0.0

        followers_following = safe_div(followers, following)
        following_followers = safe_div(following, followers)
        following_followers_square = safe_div(following, max(followers * followers, 1))
        following_total = safe_div(following, following + followers)
        followers2_following = (2 * followers) - following
        followers2_greater100 = 1.0 if (2 * followers) >= 100 else 0.0
        listed_growth_rate = safe_div(listed, active_days)
        tweet_freq = safe_div(tweet_count, active_days)
        followers_growth_rate = safe_div(followers, active_days)
        friends_growth_rate = safe_div(following, active_days)
        listed_followers = safe_div(listed, followers)
        tweets_followers = safe_div(tweet_count, followers)
        listed_tweets = safe_div(listed, tweet_count)
        relation_length_username_name = safe_div(len(username), len(display_name))
        lev_username_name = float(lev_distance(display_name, username))

        desc_len = len(description)
        entropy_name = entropy(display_name)
        entropy_username = entropy(username)

        tweet_features = {
            46: 0.0,
            47: 0.0,
            48: 0.0,
            49: 0.0,
            50: 0.0,
            51: 0.0,
            52: 0.0,
        }
        if tweets:
            all_words = []
            hashtag_counts = []
            url_counts = []
            retweets = 0
            for tweet in tweets:
                all_words.extend(tweet.split())
                hashtag_counts.append(len(re.findall(r"#\w+", tweet)))
                url_counts.append(len(re.findall(r"http[s]?://\S+", tweet)))
                if tweet.startswith("RT @"):
                    retweets += 1
            total_words = len(all_words)
            unique_words = len({word.lower() for word in all_words})
            tweet_features[49] = safe_div(unique_words, total_words)
            tweet_features[50] = sum(hashtag_counts) / len(hashtag_counts)
            tweet_features[51] = sum(url_counts) / len(url_counts)
            tweet_features[52] = safe_div(retweets, len(tweets))

        numeric_values = [
            self._scale_counts(following, "following"),
            self._scale_counts(followers, "followers"),
            self._scale_counts(tweet_count, "tweets"),
            self._scale_counts(len(username), "username_len"),
            self._scale_counts(len(display_name), "name_len", fallback_mean=11.0, fallback_std=3.0),
            math.log1p(active_days),
            self._scale_counts(listed, "listed"),
            float(hashtags_desc),
            float(desc_len),
            followers_following,
            float(hashtags_desc),
            float(urls_desc),
            tweet_freq,
            followers_growth_rate,
            friends_growth_rate,
            lev_username_name,
            relation_length_username_name,
            float(number_count_username),
            float(number_count_name),
            rel_upper_lower_username,
            rel_upper_lower_name,
            float(digits_username),
            float(digits_name),
            following_followers,
            following_followers_square,
            following_total,
            float(followers2_following),
            listed_growth_rate,
            listed_followers,
            tweets_followers,
            listed_tweets,
            0.0,
            entropy_name,
            entropy_username,
            tweet_features[46],
            tweet_features[47],
            tweet_features[48],
            tweet_features[49],
            tweet_features[50],
            tweet_features[51],
            tweet_features[52],
        ]

        num = torch.tensor([numeric_values], dtype=torch.float32)
        cat = torch.tensor([cat], dtype=torch.float32)

        description_embedding = self._mean_pool_texts([description])
        tweet_embedding = self._mean_pool_texts(tweets)

        if description_embedding.ndim == 1:
            description_embedding = description_embedding.unsqueeze(0)
        if tweet_embedding.ndim == 1:
            tweet_embedding = tweet_embedding.unsqueeze(0)

        full_feature = torch.cat([cat, num, description_embedding, tweet_embedding], dim=1)
        return full_feature

    def predict(self, payload) -> PredictionResult:
        feature = self._vectorize(payload).to(self.device)
        edge_index = torch.tensor([[0], [0]], dtype=torch.long, device=self.device)
        edge_type = torch.tensor([0], dtype=torch.long, device=self.device)

        self.model.eval()
        with torch.inference_mode():
            logits = self.model(feature, edge_index, edge_type)
            probabilities = torch.softmax(logits, dim=1)[0]

        bot_probability = float(probabilities[1].item())
        human_probability = float(probabilities[0].item())
        label = "bot" if bot_probability >= human_probability else "human"
        confidence = max(bot_probability, human_probability)

        signals = []
        if getattr(payload, "verified", False):
            signals.append("Verified account")
        if getattr(payload, "followers_count", 0) > getattr(payload, "following_count", 0):
            signals.append("Follower count is stronger than following count")
        if any("bot" in text.lower() for text in [payload.username, payload.display_name or "", payload.description or ""]):
            signals.append("Contains bot-related keywords")
        if payload.sample_tweets:
            signals.append(f"Analyzed {len(payload.sample_tweets)} sample tweets")

        return PredictionResult(
            label=label,
            confidence=confidence,
            bot_probability=bot_probability,
            human_probability=human_probability,
            signals=signals,
        )


@lru_cache(maxsize=1)
def get_predictor() -> BotPredictor:
    return BotPredictor()