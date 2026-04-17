import csv

INPUT_FILE = "bot_scores.csv"
OUTPUT_FILE = "labeled_users.csv"
THRESHOLD = 2.5

def label_users():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Write header in new file
            writer.writerow(["username", "label"])

            for row in reader:
                try:
                    # Skip empty rows
                    if len(row) < 2:
                        continue

                    username = row[0].strip()
                    score = float(row[1])

                    label = 1 if score > THRESHOLD else 0

                    writer.writerow([username, label])

                except Exception:
                    # Skip bad rows safely
                    continue

        print(f"Done! Labels saved to '{OUTPUT_FILE}'")

    except FileNotFoundError:
        print(f"Error: '{INPUT_FILE}' not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    label_users()