import json
import csv

# Configuration
INPUT_FILE = "tweets_2026-03-30_enhanced.json"
OUTPUT_FILE = "extracted_users.csv"

def extract_users():
    print(f"Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        tweets = data.get("tweets", [])
        
        # Use a dictionary to keep track of unique users
        # Key: username, Value: {id, created_at}
        unique_users = {}
        
        for tweet in tweets:
            username = tweet.get("username")
            user_id = tweet.get("user_id")
            # Some tweets have 'account_creation_date', others might have 'user_created_at'
            created_at = tweet.get("account_creation_date") or tweet.get("user_created_at")
            
            if username and username not in unique_users:
                unique_users[username] = {
                    "username": username,
                    "user_id": user_id,
                    "created_at": created_at
                }
        
        # Write to CSV for easy viewing
        fieldnames = ["username", "user_id", "created_at"]
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for user in unique_users.values():
                writer.writerow(user)
        
        print(f"Successfully extracted {len(unique_users)} unique users to {OUTPUT_FILE}.")
        
        # Also print the first 5 for the user to see
        print("\nFirst 5 extracted users:")
        for i, user in enumerate(list(unique_users.values())[:5]):
            print(f"{i+1}. {user['username']} (ID: {user['user_id']}) - Created: {user['created_at']}")

    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_users()
