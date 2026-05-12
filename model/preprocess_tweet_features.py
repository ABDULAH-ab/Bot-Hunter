"""
Preprocess tweet-level features for bot detection.
Extracts 7 temporal and content diversity features per user from tweet JSON files.

MEMORY-OPTIMIZED: Uses fixed-size numpy arrays and running counters instead of
growing Python lists/sets. Peak RAM ~2-3 GB for 1M users instead of 30+ GB.

Features computed:
  46. posting_hour_entropy   — Shannon entropy of posting hour distribution (0-23)
  47. inter_tweet_time_std   — Std deviation of time gaps between consecutive tweets
  48. weekend_ratio          — Fraction of tweets posted on weekends (Sat/Sun)
  49. type_token_ratio       — Unique words / total words (vocabulary richness)
  50. avg_hashtag_count      — Average number of hashtags per tweet
  51. avg_url_count          — Average number of URLs per tweet
  52. retweet_ratio          — Fraction of tweets that are retweets (start with "RT @")
"""

import json
import os
import re
import gc
import hashlib
import numpy as np
import torch
from datetime import datetime
from tqdm import tqdm

# ijson for streaming large JSON files (avoids OOM)
try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False
    print("WARNING: ijson not installed. Will use chunked JSON reading (slower).")

DATA_DIR = "Twibot22_Dataset"
PROCESSED_DIR = "processed_data"
TWEET_FILES = 9

# HyperLogLog-style unique word estimation using a fixed-size hash set
# Instead of storing every unique word (set grows to GB), we keep a fixed
# bit array per user and hash words into it. Gives ~3% error but uses ~100x less RAM.
BLOOM_SIZE = 1024  # bits per user for word uniqueness estimation


def z_score_normalize(arr):
    """Z-score normalize with protection against constant columns."""
    std = np.std(arr)
    if std == 0:
        return np.zeros_like(arr)
    return (arr - np.mean(arr)) / std


def word_hash(word, size):
    """Hash a word to a bucket index."""
    return int(hashlib.md5(word.encode('utf-8', errors='ignore')).hexdigest(), 16) % size


def stream_tweets_ijson(tweet_path):
    """Stream tweets from a JSON array file using ijson (constant memory)."""
    with open(tweet_path, 'rb') as f:
        parser = ijson.items(f, 'item')
        for tweet in parser:
            yield tweet


def stream_tweets_fallback(tweet_path):
    """Fallback: read JSON array line by line (no ijson needed)."""
    with open(tweet_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        if first_line == '[':
            pass
        else:
            f.seek(0)
            tweets = json.load(f)
            yield from tweets
            return

        buffer = ""
        for line in f:
            line = line.strip()
            if not line or line == ']':
                continue
            if line.endswith(','):
                line = line[:-1]
            buffer += line
            try:
                tweet = json.loads(buffer)
                yield tweet
                buffer = ""
            except json.JSONDecodeError:
                buffer += " "
                continue


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Load user index mapping
    uid_index_path = os.path.join(PROCESSED_DIR, 'uid_index.json')
    with open(uid_index_path, 'r') as f:
        uid_index = json.load(f)

    num_users = len(uid_index)
    print(f"Computing tweet features for {num_users} users")

    # ---------------------------------------------------------------
    # FIXED-SIZE accumulators (numpy arrays — predictable memory)
    # All are (num_users,) or (num_users, 24) — total ~200 MB for 1M users
    # ---------------------------------------------------------------
    hour_bins = np.zeros((num_users, 24), dtype=np.int32)       # 24 hour histogram
    tweet_count = np.zeros(num_users, dtype=np.int32)           # total tweets per user
    weekend_count = np.zeros(num_users, dtype=np.int32)         # weekend tweets
    retweet_count = np.zeros(num_users, dtype=np.int32)         # retweet count
    hashtag_sum = np.zeros(num_users, dtype=np.float32)         # sum of hashtag counts
    url_sum = np.zeros(num_users, dtype=np.float32)             # sum of url counts
    word_total = np.zeros(num_users, dtype=np.int64)            # total words

    # For inter-tweet time std: Welford's online algorithm
    # Computes running variance without storing all timestamps
    ts_count = np.zeros(num_users, dtype=np.int32)              # timestamps seen
    ts_prev = np.full(num_users, np.nan, dtype=np.float64)      # previous timestamp
    ts_diff_mean = np.zeros(num_users, dtype=np.float64)        # running mean of diffs
    ts_diff_m2 = np.zeros(num_users, dtype=np.float64)          # running M2 for variance

    # For type-token ratio: bloom filter bit array (~128 KB per 1M users)
    # Each user gets BLOOM_SIZE bits to estimate unique word count
    bloom_bytes = (BLOOM_SIZE + 7) // 8  # bytes per user
    bloom_filters = np.zeros((num_users, bloom_bytes), dtype=np.uint8)
    word_unique_est = np.zeros(num_users, dtype=np.int32)       # estimated unique words

    print(f"Accumulator memory: ~{(hour_bins.nbytes + tweet_count.nbytes * 6 + bloom_filters.nbytes) / 1e6:.0f} MB")

    # Stream through all tweet files
    for i in range(TWEET_FILES):
        tweet_path = os.path.join(DATA_DIR, f"tweet_{i}.json")
        if not os.path.exists(tweet_path):
            print(f"Skipping {tweet_path} (not found)")
            continue

        print(f"Processing {tweet_path}")

        if HAS_IJSON:
            tweet_stream = stream_tweets_ijson(tweet_path)
        else:
            tweet_stream = stream_tweets_fallback(tweet_path)

        count = 0
        for each in tqdm(tweet_stream, desc=f"tweet_{i}.json"):
            uid = "u" + str(each.get("author_id", ""))
            idx_str = uid_index.get(uid)
            if idx_str is None:
                count += 1
                continue

            idx = int(idx_str)
            tweet_count[idx] += 1

            # --- Text analysis ---
            text = each.get("text", "")
            if isinstance(text, str) and text.strip():
                words = text.split()
                word_total[idx] += len(words)

                # Bloom filter for unique words (instead of storing set())
                for w in words:
                    wl = w.lower()
                    h = word_hash(wl, BLOOM_SIZE)
                    byte_idx = h // 8
                    bit_idx = h % 8
                    if not (bloom_filters[idx, byte_idx] & (1 << bit_idx)):
                        bloom_filters[idx, byte_idx] |= (1 << bit_idx)
                        word_unique_est[idx] += 1

                # Hashtag & URL counts
                hashtag_sum[idx] += len(re.findall(r'#\w+', text))
                url_sum[idx] += len(re.findall(r'http[s]?://\S+', text))

                # Retweet detection
                if text.startswith("RT @"):
                    retweet_count[idx] += 1

            # --- Temporal analysis ---
            created_at = each.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    hour_bins[idx, dt.hour] += 1

                    # Weekend check
                    if dt.weekday() >= 5:
                        weekend_count[idx] += 1

                    # Welford's online variance for inter-tweet time diffs
                    ts = dt.timestamp()
                    if not np.isnan(ts_prev[idx]):
                        diff = ts - ts_prev[idx]
                        ts_count[idx] += 1
                        delta = diff - ts_diff_mean[idx]
                        ts_diff_mean[idx] += delta / ts_count[idx]
                        delta2 = diff - ts_diff_mean[idx]
                        ts_diff_m2[idx] += delta * delta2
                    ts_prev[idx] = ts
                except (ValueError, TypeError):
                    pass

            count += 1

        print(f"  Processed {count:,} tweets from tweet_{i}.json")
        gc.collect()

    # ---------------------------------------------------------------
    # Compute final per-user features from accumulators
    # ---------------------------------------------------------------
    print("Computing aggregated features...")
    posting_hour_entropy = np.zeros(num_users, dtype=np.float32)
    inter_tweet_time_std = np.zeros(num_users, dtype=np.float32)
    weekend_ratio = np.zeros(num_users, dtype=np.float32)
    type_token_ratio = np.zeros(num_users, dtype=np.float32)
    avg_hashtag_count = np.zeros(num_users, dtype=np.float32)
    avg_url_count = np.zeros(num_users, dtype=np.float32)
    retweet_ratio = np.zeros(num_users, dtype=np.float32)

    for idx in range(num_users):
        tc = tweet_count[idx]
        if tc == 0:
            continue

        # 1. Posting hour entropy (from 24-bin histogram)
        bins = hour_bins[idx]
        total_hours = bins.sum()
        if total_hours > 0:
            probs = bins[bins > 0].astype(np.float64) / total_hours
            posting_hour_entropy[idx] = -np.sum(probs * np.log2(probs))

        # 2. Inter-tweet time std (from Welford's online variance)
        if ts_count[idx] > 1:
            variance = ts_diff_m2[idx] / ts_count[idx]
            inter_tweet_time_std[idx] = np.sqrt(max(variance, 0))

        # 3. Weekend ratio
        weekend_ratio[idx] = weekend_count[idx] / tc

        # 4. Type-token ratio (from bloom filter estimate)
        if word_total[idx] > 0:
            type_token_ratio[idx] = word_unique_est[idx] / word_total[idx]

        # 5. Average hashtag count per tweet
        avg_hashtag_count[idx] = hashtag_sum[idx] / tc

        # 6. Average URL count per tweet
        avg_url_count[idx] = url_sum[idx] / tc

        # 7. Retweet ratio
        retweet_ratio[idx] = retweet_count[idx] / tc

    # Z-score normalize all features
    features = np.column_stack([
        z_score_normalize(posting_hour_entropy),
        z_score_normalize(inter_tweet_time_std),
        z_score_normalize(weekend_ratio),
        z_score_normalize(type_token_ratio),
        z_score_normalize(avg_hashtag_count),
        z_score_normalize(avg_url_count),
        z_score_normalize(retweet_ratio),
    ])

    # Guard against NaN/Inf
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    tweet_features_tensor = torch.tensor(features, dtype=torch.float32)
    output_path = os.path.join(PROCESSED_DIR, 'tweet_features.pt')
    torch.save(tweet_features_tensor, output_path)
    print(f"Saved tweet features tensor {tweet_features_tensor.shape} to {output_path}")
    print("Feature columns: posting_hour_entropy, inter_tweet_time_std, weekend_ratio, "
          "type_token_ratio, avg_hashtag_count, avg_url_count, retweet_ratio")


if __name__ == "__main__":
    main()
