import gc
import json
import os

import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

# Try to import ijson for streaming JSON parsing (optional optimization)
try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False


DATA_DIR = "Twibot22_Dataset"
PROCESSED_DIR = "processed_data"
MAX_LEN = 50
MAX_TWEETS_PER_USER = int(os.getenv("MAX_TWEETS_PER_USER", "20"))
BATCH_SIZE = max(1, int(os.getenv("BATCH_SIZE", "8")))
GC_INTERVAL = max(1, int(os.getenv("GC_INTERVAL", "500")))
LOG_INTERVAL = max(1, int(os.getenv("LOG_INTERVAL", "50000")))
MODEL_NAME = os.getenv("TEXT_MODEL", "roberta-base")
TWEET_FILES = 9
FORCE_REBUILD = os.getenv("FORCE_REBUILD", "0") == "1"
IS_BERTWEET = "bertweet" in MODEL_NAME.lower()


def normalize_for_bertweet(text):
    """Normalize text for BERTweet tokenizer expectations.
    BERTweet was trained with @mentions replaced by @USER,
    URLs replaced by HTTPURL, and emojis converted to text."""
    import re
    # Replace @mentions with @USER
    text = re.sub(r'@\w+', '@USER', text)
    # Replace URLs with HTTPURL
    text = re.sub(r'http\S+', 'HTTPURL', text)
    # Convert emojis to text (optional dependency)
    try:
        from emoji import demojize
        text = demojize(text, delimiters=(' ', ' '))
    except ImportError:
        pass
    return text


def build_encoder():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device)
    model.eval()
    return tokenizer, model, device


def encode_texts(texts, tokenizer, model, device):
    # Normalize for BERTweet if applicable
    if IS_BERTWEET:
        texts = [normalize_for_bertweet(t) for t in texts]

    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=MAX_LEN,
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.inference_mode():
        hidden = model(**inputs).last_hidden_state
        mask = inputs["attention_mask"].unsqueeze(-1)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)

    return pooled.cpu()


def flush_batch(tokenizer, model, device, texts, indices, sum_tensor, count_tensor):
    if not texts:
        return 0, 0

    processed = 0
    newly_full = 0
    try:
        pooled = encode_texts(texts, tokenizer, model, device)
        for idx, vec in zip(indices, pooled):
            if count_tensor[idx].item() >= MAX_TWEETS_PER_USER:
                continue
            sum_tensor[idx] += vec
            count_tensor[idx] += 1
            processed += 1
            if count_tensor[idx].item() == MAX_TWEETS_PER_USER:
                newly_full += 1
        return processed, newly_full
    finally:
        texts.clear()
        indices.clear()


def description_embedding(tokenizer, model, device, user_text, output_path):
    print("Running description embedding")
    num_users = len(user_text)
    des_tensor = torch.zeros((num_users, 768), dtype=torch.float32)

    processed_batches = 0
    for start in tqdm(range(0, num_users, BATCH_SIZE)):
        end = min(start + BATCH_SIZE, num_users)
        batch = user_text[start:end]

        valid_indices = []
        valid_texts = []
        for i, text in enumerate(batch):
            if isinstance(text, str) and text.strip():
                valid_indices.append(start + i)
                valid_texts.append(text)

        if not valid_texts:
            continue

        try:
            pooled = encode_texts(valid_texts, tokenizer, model, device)
            for idx, vec in zip(valid_indices, pooled):
                des_tensor[idx] = vec
            processed_batches += 1
            if processed_batches % GC_INTERVAL == 0:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        finally:
            valid_texts.clear()
            valid_indices.clear()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    torch.save(des_tensor, output_path)
    print(f"Saved description tensor to {output_path}")


def tweets_embedding_stream(tokenizer, model, device, uid_index, num_users, output_path):
    print("Running tweets embedding")
    sum_tensor = torch.zeros((num_users, 768), dtype=torch.float32)
    count_tensor = torch.zeros(num_users, dtype=torch.int32)

    pending_texts = []
    pending_indices = []
    processed_items = 0
    full_users = 0
    target_users = num_users
    scanned_items = 0

    for i in range(TWEET_FILES):
        tweet_path = os.path.join(DATA_DIR, f"tweet_{i}.json")
        print(f"Processing {tweet_path}")
        
        # Use ijson for memory-efficient streaming if available
        if HAS_IJSON:
            with open(tweet_path, "rb") as f:
                for each in ijson.items(f, "item"):
                    scanned_items += 1
                    uid = "u" + str(each["author_id"])
                    idx = uid_index.get(uid)
                    if idx is None or count_tensor[idx].item() >= MAX_TWEETS_PER_USER:
                        if scanned_items % LOG_INTERVAL == 0:
                            print(
                                f"Scanned={scanned_items:,} | Encoded={processed_items:,} | "
                                f"UsersFull={full_users:,}/{target_users:,}"
                            )
                        continue

                    text = each.get("text")
                    if not isinstance(text, str) or not text.strip():
                        continue

                    pending_texts.append(text)
                    pending_indices.append(idx)

                    if len(pending_texts) >= max(1, BATCH_SIZE):
                        n_processed, n_full = flush_batch(tokenizer, model, device, pending_texts, pending_indices, sum_tensor, count_tensor)
                        processed_items += n_processed
                        full_users += n_full
                        if processed_items % GC_INTERVAL == 0:
                            gc.collect()
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                    if scanned_items % LOG_INTERVAL == 0:
                        print(
                            f"Scanned={scanned_items:,} | Encoded={processed_items:,} | "
                            f"UsersFull={full_users:,}/{target_users:,}"
                        )
                        if full_users >= target_users:
                            break
        else:
            # Fallback: load entire file but with aggressive cleanup every 1000 tweets
            with open(tweet_path, "r", encoding="utf-8") as f:
                user_tweets = json.load(f)
            
            total_tweets = len(user_tweets)
            for idx, each in enumerate(tqdm(user_tweets, desc=f"tweet_{i}.json", total=total_tweets)):
                uid = "u" + str(each["author_id"])
                user_idx = uid_index.get(uid)
                if user_idx is None or count_tensor[user_idx].item() >= MAX_TWEETS_PER_USER:
                    continue

                text = each.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue

                pending_texts.append(text)
                pending_indices.append(user_idx)

                if len(pending_texts) >= max(1, BATCH_SIZE):
                    n_processed, n_full = flush_batch(tokenizer, model, device, pending_texts, pending_indices, sum_tensor, count_tensor)
                    processed_items += n_processed
                    full_users += n_full
                    if processed_items % GC_INTERVAL == 0:
                        gc.collect()
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    if full_users >= target_users:
                        break
                
                # Keep periodic cleanup in the JSON fallback path too.
                if (idx + 1) % (GC_INTERVAL * 2) == 0:
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
            
            del user_tweets
            gc.collect()
        
        n_processed, n_full = flush_batch(tokenizer, model, device, pending_texts, pending_indices, sum_tensor, count_tensor)
        processed_items += n_processed
        full_users += n_full
        print(
            f"Completed file tweet_{i}.json | Scanned={scanned_items:,} | Encoded={processed_items:,} | "
            f"UsersFull={full_users:,}/{target_users:,}"
        )
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if full_users >= target_users:
            print("Reached max tweets for all users. Stopping early.")
            break

    tweet_tensor = torch.zeros((num_users, 768), dtype=torch.float32)
    non_zero = count_tensor > 0
    tweet_tensor[non_zero] = sum_tensor[non_zero] / count_tensor[non_zero].unsqueeze(1).float()

    torch.save(tweet_tensor, output_path)
    print(f"Saved tweet tensor to {output_path}")


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    user = pd.read_json(os.path.join(DATA_DIR, "user.json"))
    user_text = list(user["description"])

    user_idx = user["id"]
    uid_index = {uid: index for index, uid in enumerate(user_idx.values)}

    tokenizer, model, device = build_encoder()
    print(f"Using {'GPU' if device.type == 'cuda' else 'CPU'} for text embedding")

    description_output = os.path.join(PROCESSED_DIR, "des_tensor.pt")
    tweets_output = os.path.join(PROCESSED_DIR, "tweets_tensor.pt")

    if os.path.exists(description_output) and not FORCE_REBUILD:
        print(f"Skipping description embedding (found {description_output})")
    else:
        description_embedding(tokenizer, model, device, user_text, description_output)

    if os.path.exists(tweets_output) and not FORCE_REBUILD:
        print(f"Skipping tweets embedding (found {tweets_output})")
    else:
        tweets_embedding_stream(tokenizer, model, device, uid_index, len(user_idx), tweets_output)

    print("Finished")


if __name__ == "__main__":
    main()
