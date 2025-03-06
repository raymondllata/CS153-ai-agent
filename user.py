import json
import os
import random

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


# def load_users():
#     """Load users from a JSON file."""
#     if os.path.exists(USER_DATA_FILE):
#         with open(USER_DATA_FILE, "r") as f:
#             return json.load(f)
#     return {}


# def save_users(users):
#     """Save user data to a JSON file."""
#     with open(USER_DATA_FILE, "w") as f:
#         json.dump(users, f, indent=4)

def make_random_user():
    """Generate a random user for testing purposes."""
    
    # Random name generation
    first_names = ["Alex", "Jordan", "Morgan", "Sam", "Taylor", "Casey", "Quinn", "Riley", "Sage", "Avery"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    # Character classes and their typical starting abilities
    character_classes = ["Warrior", "Mage", "Rogue", "Cleric"]
    
    # Generate random components
    user_id = random.randint(10000, 99999)
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    character_class = random.choice(character_classes)
    level = random.randint(1, 5)  # Random starting level between 1-5
    
    # Create the user
    user = User(user_id, name, character_class, level)
    
    # Randomize base stats based on character class
    class_stat_preferences = {
        "Warrior": ["Strength", "Constitution"],
        "Mage": ["Intelligence", "Wisdom"],
        "Rogue": ["Dexterity", "Charisma"],
        "Cleric": ["Wisdom", "Charisma"]
    }
    
    # Adjust stats based on class preference
    preferred_stats = class_stat_preferences[character_class]
    for stat in user.stats:
        base_value = random.randint(8, 12)  # Base random stat
        if stat in preferred_stats:
            base_value += random.randint(2, 4)  # Bonus for class-preferred stats
        user.stats[stat] = min(20, base_value)  # Cap at 20
    
    # Add some random starting items
    possible_items = [
        "Health Potion",
        "Mana Potion",
        "Iron Sword",
        "Leather Armor",
        "Magic Scroll",
        "Shield",
        "Healing Herbs",
        "Magic Wand"
    ]
    
    # Add 2-4 random items
    num_items = random.randint(2, 4)
    for _ in range(num_items):
        user.add_item(random.choice(possible_items))
    
    # Add some basic abilities based on class
    class_abilities = {
        "Warrior": ["Slash", "Shield Block", "Battle Cry"],
        "Mage": ["Fireball", "Frost Nova", "Arcane Missile"],
        "Rogue": ["Backstab", "Stealth", "Poison Strike"],
        "Cleric": ["Heal", "Smite", "Bless"]
    }
    
    user.abilities = random.sample(class_abilities[character_class], 2)
    
    return user

# def get_user(user_id):
#     """Retrieve a user from storage or create a new one."""
#     # users = load_users()
#     if str(user_id) in users:
#         user_data = users[str(user_id)]
#         return User(user_id, user_data["name"], user_data["character_class"], user_data["level"])
    
#     # Create a new user if they don't exist
#     new_user = User(user_id, "New Player", "Warrior")
#     users[str(user_id)] = {
#         "name": new_user.name,
#         "character_class": new_user.character_class,
#         "level": new_user.level
#     }
#     # save_users(users)
#     return new_user

def parse_character_json(json_string):
    """
    Parses a JSON string containing character data and returns a User object.
    
    Args:
        json_string (str): JSON string containing character data
        
    Returns:
        User: A fully initialized User object based on the JSON data
    """
    try:
        import json
        import random
        
        # Debug prints
        print("Received JSON string type:", type(json_string))
        print("JSON string length:", len(str(json_string)) if json_string else 0)
        
        # Check if the string is empty or None
        if not json_string:
            print("Empty JSON string received, creating random user")
            return make_random_user()
            
        # If the string looks like it already has the JSON parsed (might be a dict)
        if isinstance(json_string, dict):
            char_data = json_string
            print("Input was already a dictionary")
        else:
            # Handle different formats - try to extract JSON if wrapped in other text
            json_string = str(json_string).strip()
            
            # Look for JSON brackets if there might be extra text
            start_idx = json_string.find('{')
            end_idx = json_string.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_string = json_string[start_idx:end_idx+1]
                print("Extracted JSON from string")
            
            print("Parsing JSON string:", json_string[:100] + "..." if len(json_string) > 100 else json_string)
            
            # Parse the JSON string
            char_data = json.loads(json_string)
        
        # Generate a random user ID
        user_id = random.randint(10000, 99999)
        
        # Create a new User object with basic info
        user = User(
            user_id=user_id,
            name=char_data.get("name", "Unknown Adventurer"),
            character_class=char_data.get("character_class", "Warrior"),
            level=char_data.get("level", 1)
        )
        
        # Add stats
        if "stats" in char_data and isinstance(char_data["stats"], dict):
            for stat, value in char_data["stats"].items():
                if stat in user.stats:
                    # Ensure stats are within valid range (8-20)
                    user.stats[stat] = max(8, min(20, int(value)))
        
        # Add inventory items
        if "inventory" in char_data and isinstance(char_data["inventory"], list):
            for item in char_data["inventory"]:
                user.add_item(item)
        
        # Add abilities
        if "abilities" in char_data and isinstance(char_data["abilities"], list):
            user.abilities = char_data["abilities"]
        
        # Add background as a property if it exists
        if "background" in char_data:
            user.background = char_data["background"]
        
        print(f"Successfully created character: {user.name}, {user.character_class}")
        return user
    except Exception as e:
        import traceback
        print(f"Error parsing character JSON: {e}")
        print(f"JSON string (first 200 chars): {str(json_string)[:200]}")
        print(traceback.format_exc())
        # Return a default user if parsing fails
        return make_random_user()
