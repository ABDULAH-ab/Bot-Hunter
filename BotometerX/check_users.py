import json
import botometer
import csv
import os

# Configuration
RAPIDAPI_KEY = "40b3cec6e7mshcbf7a6732f9c248p178266jsn230f4ddd6c39"
FILE_PATH = "user_profile_cache.json"
OUTPUT_FILE = "bot_scores.csv"
BATCH_SIZE = 100

def extract_username(tweet):
    """Handles different JSON structures"""
    return (
        tweet.get('username') or
        tweet.get('user_name') or
        tweet.get('screen_name') or
        tweet.get('user', {}).get('screen_name') or
        tweet.get('user', {}).get('username')
    )

def run_check():
    try:
        # 1. Load tweet data
        with open(FILE_PATH, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        tweets = data.get('tweets', [])

        # 2. Extract usernames safely
        usernames = set()

        for tweet in tweets:
            username = extract_username(tweet)
            if username:
                usernames.add(username)

        print(f"Total unique users found in this file: {len(usernames)}")

        # 3. Load existing users safely
        existing_users = set()

        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    # Normalize header names
                    fieldnames = [name.strip().lower() for name in reader.fieldnames]

                    for row in reader:
                        for key in row:
                            if key.strip().lower() == "username":
                                existing_users.add(row[key])
                                break
            except Exception:
                print("Warning: Could not read existing CSV properly. Continuing...")

        print(f"Already processed users: {len(existing_users)}")

        # 4. Filter new users
        new_usernames = list(usernames - existing_users)
        print(f"New users to process: {len(new_usernames)}")

        if not new_usernames:
            print("No new users found.")
            return

        # 5. Initialize Botometer
        bomx = botometer.BotometerX(rapidapi_key=RAPIDAPI_KEY)

        bot_scores = {}

        total_batches = (len(new_usernames) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(total_batches):
            start = batch_num * BATCH_SIZE
            end = start + BATCH_SIZE
            batch = new_usernames[start:end]

            print(f"\nProcessing batch {batch_num + 1}/{total_batches}...")

            try:
                results = bomx.get_botscores_in_batch(usernames=batch)

                for res in results:
                    username = res.get('username')
                    score = res.get('bot_score')

                    if username and score is not None:
                        bot_scores[username] = score

            except Exception as batch_err:
                print(f"Error in batch {batch_num + 1}: {batch_err}")
                continue

        # 6. Append to CSV safely
        file_exists = os.path.exists(OUTPUT_FILE)

        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            if not file_exists:
                writer.writerow(["username", "bot_score"])

            for username, score in bot_scores.items():
                writer.writerow([username, score])

        print(f"\nDone! {len(bot_scores)} new users added.")

    except FileNotFoundError:
        print(f"Error: Could not find '{FILE_PATH}'")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    run_check()