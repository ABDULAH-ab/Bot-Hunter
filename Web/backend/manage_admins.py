#!/usr/bin/env python3
"""
Admin User Management Script
This script allows you to promote users to admin or demote them.
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_hunter")

def get_db():
    """Connect to MongoDB"""
    client = MongoClient(MONGODB_URL, tlsAllowInvalidCertificates=True)
    return client[DATABASE_NAME]

def list_users(db):
    """List all users"""
    print("\n=== All Users ===")
    users = db.users.find({}, {"username": 1, "email": 1, "is_admin": 1, "created_at": 1})
    
    print(f"{'ID':<26} {'Username':<20} {'Email':<30} {'Admin':<8} {'Created'}")
    print("-" * 100)
    
    for user in users:
        user_id = str(user["_id"])
        username = user.get("username", "N/A")
        email = user.get("email", "N/A")
        is_admin = "Yes" if user.get("is_admin", False) else "No"
        created = user.get("created_at", "N/A")
        
        print(f"{user_id:<26} {username:<20} {email:<30} {is_admin:<8} {created}")
    print()

def make_admin(db, identifier):
    """Promote user to admin by username or email"""
    # Try to find by username or email
    user = db.users.find_one({
        "$or": [
            {"username": identifier},
            {"email": identifier}
        ]
    })
    
    if not user:
        print(f"❌ User '{identifier}' not found")
        return False
    
    if user.get("is_admin", False):
        print(f"ℹ️  User '{identifier}' is already an admin")
        return True
    
    # Update user to admin
    result = db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "is_admin": True,
                "admin_since": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"✅ Successfully promoted '{identifier}' to admin")
        return True
    else:
        print(f"❌ Failed to promote '{identifier}' to admin")
        return False

def remove_admin(db, identifier):
    """Demote admin user by username or email"""
    # Try to find by username or email
    user = db.users.find_one({
        "$or": [
            {"username": identifier},
            {"email": identifier}
        ]
    })
    
    if not user:
        print(f"❌ User '{identifier}' not found")
        return False
    
    if not user.get("is_admin", False):
        print(f"ℹ️  User '{identifier}' is not an admin")
        return True
    
    # Remove admin privileges
    result = db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "is_admin": False,
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "admin_since": ""
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"✅ Successfully removed admin privileges from '{identifier}'")
        return True
    else:
        print(f"❌ Failed to remove admin privileges from '{identifier}'")
        return False

def interactive_mode(db):
    """Interactive mode for admin management"""
    print("\n" + "="*50)
    print("Bot Hunter - Admin User Management")
    print("="*50)
    
    while True:
        print("\nOptions:")
        print("1. List all users")
        print("2. Promote user to admin")
        print("3. Remove admin privileges")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            list_users(db)
        
        elif choice == "2":
            identifier = input("Enter username or email to promote: ").strip()
            if identifier:
                make_admin(db, identifier)
        
        elif choice == "3":
            identifier = input("Enter username or email to demote: ").strip()
            if identifier:
                remove_admin(db, identifier)
        
        elif choice == "4":
            print("\nGoodbye! 👋")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

def main():
    """Main function"""
    db = get_db()
    
    # Check command line arguments
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode(db)
    
    elif len(sys.argv) == 3:
        action = sys.argv[1].lower()
        identifier = sys.argv[2]
        
        if action == "add" or action == "promote":
            make_admin(db, identifier)
        
        elif action == "remove" or action == "demote":
            remove_admin(db, identifier)
        
        elif action == "list":
            list_users(db)
        
        else:
            print(f"❌ Unknown action: {action}")
            print_usage()
    
    else:
        print_usage()

def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  Interactive mode:    python3 manage_admins.py")
    print("  Promote to admin:    python3 manage_admins.py add <username_or_email>")
    print("  Remove admin:        python3 manage_admins.py remove <username_or_email>")
    print("  List users:          python3 manage_admins.py list")
    print("\nExamples:")
    print("  python3 manage_admins.py add john@example.com")
    print("  python3 manage_admins.py remove johndoe")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
