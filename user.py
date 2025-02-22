import json
import os

USER_DATA_FILE = "users.json"

class User:
    def __init__(self, user_id: int, name: str, character_class: str, level: int = 1):
        self.user_id = user_id
        self.name = name
        self.character_class = character_class
        self.level = level
        self.stats = {
            "Strength": 10,
            "Dexterity": 10,
            "Constitution": 10,
            "Intelligence": 10,
            "Wisdom": 10,
            "Charisma": 10,
        }
        self.inventory = []
        self.abilities = []

    def level_up(self):
        """Increase the user's level and boost stats."""
        self.level += 1
        self.stats["Strength"] += 1
        self.stats["Dexterity"] += 1
        return f"{self.name} has leveled up to Level {self.level}!"

    def add_item(self, item: str):
        """Add an item to the user's inventory."""
        self.inventory.append(item)
        return f"{self.name} received {item}!"

    def show_stats(self):
        """Display user stats."""
        return f"Name: {self.name}\nClass: {self.character_class}\nLevel: {self.level}\nStats: {self.stats}\nInventory: {self.inventory}"

def load_users():
    """Load users from a JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

'''
def save_users(users):
    """Save user data to a JSON file."""
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)
'''

def get_user(user_id):
    """Retrieve a user from storage or create a new one."""
    users = load_users()
    if str(user_id) in users:
        user_data = users[str(user_id)]
        return User(user_id, user_data["name"], user_data["character_class"], user_data["level"])
    
    # Create a new user if they don't exist
    new_user = User(user_id, "New Player", "Warrior")
    users[str(user_id)] = {
        "name": new_user.name,
        "character_class": new_user.character_class,
        "level": new_user.level
    }
    # save_users(users)
    return new_user
