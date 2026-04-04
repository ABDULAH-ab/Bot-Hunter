"""
prepare_scraped_for_tmtm.py
----------------------------
Converts tweets_*_enhanced.json (scraped format) into the file structure
that TMTM's preprocess_features.py and preprocess_text.py expect:

  processed_data/
    uid_index.json          <- built by preprocess_features.py (no action needed)

  Twibot22_Dataset/
    user.json               <- one record per user, TMTM schema
    tweet_0.json            <- tweets in TMTM schema  (author_id = numeric-style uid)
    label.csv               <- dummy labels (all "human") — replace with real labels

Usage:
    python prepare_scraped_for_tmtm.py --input tweets_2026-03-30_enhanced.json
                                       --out_dir Twibot22_Dataset

After running this script, execute TMTM's pipeline in order:
    python preprocess_features.py
    python preprocess_text.py
    python preprocess_relations.py   # skip if you have no edge data
"""

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_date_to_unix(date_str: str) -> float:
    """
    Convert ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ) to Unix
    timestamp (seconds since epoch). Returns 0.0 on failure.
    """
    if not date_str:
        return 0.0
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return 0.0


def make_user_id(username: str) -> str:
    """
    TMTM expects user IDs in the form 'u<numeric_id>'.
    Since scraped data has only usernames, we fabricate a stable numeric ID
    by hashing the username. This is consistent across runs.
    """
    return "u" + str(abs(hash(username)) % (10 ** 12))


def make_public_metrics(row: dict) -> dict:
    """Nest flat count fields into the public_metrics dict TMTM expects."""
    return {
        "followers_count": int(row.get("followers_count") or 0),
        "following_count": int(row.get("following_count") or 0),
        "tweet_count":     int(row.get("tweet_count") or 0),
        "listed_count":    int(row.get("listed_count") or 0),
    }


def make_entities(_row: dict) -> dict:
    """
    TMTM's preprocess_features.py reads entities['description']['hashtags'].
    We have no real entity data from the scraper, so return an empty structure.
    preprocess_features.py wraps the access in try/except, so this safely
    yields num_of_hashtags = 0.
    """
    return {"description": {}}


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def build_user_and_tweet_records(tweets: list[dict]):
    """
    Deduplicate tweets by user and build:
      - user_records  : list of dicts in TMTM user.json schema
      - tweet_records : list of dicts in TMTM tweet_*.json schema
    """

    # Group tweets by username (stable key from scraper)
    by_user: dict[str, list[dict]] = defaultdict(list)
    for t in tweets:
        by_user[t["username"]].append(t)

    user_records = []
    tweet_records = []

    for username, user_tweets in by_user.items():
        # Use the first tweet's user metadata as the canonical user record
        ref = user_tweets[0]

        uid = make_user_id(username)

        # ---- user.json record ----
        user_rec = {
            # Identity
            "id":       uid,
            "username": username,
            "name":     ref.get("display_name") or username,   # display_name -> name

            # Bio / description (TMTM calls this 'description')
            "description": ref.get("bio") or "",

            # created_at as Unix timestamp (what preprocess_features.py expects)
            "created_at": iso_date_to_unix(ref.get("user_created_at")),

            # Public metrics nested dict
            "public_metrics": make_public_metrics(ref),

            # --- Fields that were not scraped; zero-filled / nulled safely ---
            # preprocess_features.py reads these but wraps in try/except or
            # checks for None, so missing == False/0 is handled gracefully.
            "protected":         False,          # cat_prop[6]  -> 0
            "verified":          bool(ref.get("verified", False)),  # cat_prop[7]
            "profile_image_url": None,           # cat_prop[8]  -> default_profile_image=1
            "location":          ref.get("location") or None,  # cat_prop[11]
            "url":               "",             # cat_prop[13] -> has_url=0
            "pinned_tweet_id":   float("nan"),   # cat_prop[27] -> has_pinned_tweet=0
            "entities":          make_entities(ref),  # num_prop[12] -> num_of_hashtags=0
        }
        user_records.append(user_rec)

        # ---- tweet_0.json records ----
        # preprocess_text.py reads: tweet["author_id"] and tweet["text"]
        # author_id stored WITHOUT the leading "u" prefix (added back in preprocess_text.py)
        numeric_id = uid[1:]   # strip leading "u"
        for t in user_tweets:
            tweet_rec = {
                "author_id": numeric_id,
                "text":      t.get("text") or "",
                # Extra fields are ignored by TMTM but kept for traceability
                "tweet_id":  t.get("tweet_id", ""),
                "timestamp": t.get("timestamp", ""),
            }
            tweet_records.append(tweet_rec)

    return user_records, tweet_records


def build_dummy_labels(user_records: list[dict]) -> pd.DataFrame:
    """
    TMTM's preprocess_features.py requires a label.csv with columns [id, label].
    Since scraped data has no ground-truth labels, we default to 'human'.
    Replace with real labels before training.
    """
    return pd.DataFrame({
        "id":    [u["id"] for u in user_records],
        "label": ["human"] * len(user_records),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convert scraped tweets JSON to TMTM dataset format.")
    parser.add_argument("--input",   default="tweets_2026-03-30_enhanced.json",
                        help="Path to the enhanced scraped JSON file")
    parser.add_argument("--out_dir", default="Twibot22_Dataset",
                        help="Output directory (TMTM expects 'Twibot22_Dataset')")
    args = parser.parse_args()

    # ---- Load input ----
    print(f"Loading {args.input} ...")
    with open(args.input, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)

    # Support both {"tweets": [...]} wrapper and bare list
    tweets = raw["tweets"] if isinstance(raw, dict) and "tweets" in raw else raw
    print(f"  {len(tweets)} tweet records, "
          f"{len({t['username'] for t in tweets})} unique users")

    # ---- Build records ----
    user_records, tweet_records = build_user_and_tweet_records(tweets)
    print(f"  Built {len(user_records)} user records, {len(tweet_records)} tweet records")

    # ---- Write output files ----
    os.makedirs(args.out_dir, exist_ok=True)

    # user.json
    user_path = os.path.join(args.out_dir, "user.json")
    pd.DataFrame(user_records).to_json(user_path, orient="records", indent=2)
    print(f"  Wrote {user_path}")

    # tweet_0.json  (single file; TMTM iterates tweet_0..tweet_8)
    tweet_path = os.path.join(args.out_dir, "tweet_0.json")
    with open(tweet_path, "w", encoding="utf-8-sig") as f:
        json.dump(tweet_records, f, indent=2)
    print(f"  Wrote {tweet_path}")

    # label.csv
    label_df = build_dummy_labels(user_records)
    label_path = os.path.join(args.out_dir, "label.csv")
    label_df.to_csv(label_path, index=False)
    print(f"  Wrote {label_path}  (dummy labels — replace before training!)")

    # ---- Sanity check ----
    print("\nSanity check — first user record:")
    sample = user_records[0]
    for k, v in sample.items():
        print(f"  {k:20s}: {repr(v)[:80]}")

    print("\nSanity check — first tweet record:")
    sample_t = tweet_records[0]
    for k, v in sample_t.items():
        print(f"  {k:20s}: {repr(v)[:80]}")

    print("\nDone. You can now run TMTM's pipeline:")
    print("  python preprocess_features.py")
    print("  python preprocess_text.py")
    print("  python preprocess_relations.py   # only if you have edge.csv")


if __name__ == "__main__":
    main()
