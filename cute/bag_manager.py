import json
import os

def ensure_bag_file_exists():
    if not os.path.exists("bag.json"):
        with open("bag.json", "w") as f:
            json.dump({}, f)

def read_user_bag(user_id):
    ensure_bag_file_exists()
    with open("bag.json", "r") as f:
        user_bag = json.load(f)
        return user_bag.get(user_id, {})

def update_user_bag(user_id, user_bag):
    ensure_bag_file_exists()
    with open("bag.json", "r") as f:
        all_user_bags = json.load(f)

    all_user_bags[user_id] = user_bag

    with open("bag.json", "w") as f:
        json.dump(all_user_bags, f)
