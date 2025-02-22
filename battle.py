from typing import List, Dict
import random

class Monster:
    def __init__(self, name: str, hp: int, attack: int, defense: int):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.defense = defense
        
    def is_alive(self) -> bool:
        return self.current_hp > 0

class Battle:
    def __init__(self):
        # Placeholder monsters that could be replaced with API calls
        self.monster_templates = [
            {"name": "Goblin", "hp": 20, "attack": 5, "defense": 2},
            {"name": "Orc", "hp": 35, "attack": 8, "defense": 4},
            {"name": "Dragon", "hp": 100, "attack": 15, "defense": 8}
        ]
        
        # Placeholder settings that could be replaced with API calls
        self.settings = [
            "Dark Forest",
            "Ancient Ruins",
            "Volcanic Cave",
            "Haunted Castle"
        ]
        
        # Placeholder storylines that could be replaced with API calls
        self.storylines = [
            "A mysterious fog surrounds you as creatures emerge from the shadows...",
            "The ancient guardian awakens, protecting its sacred grounds...",
            "You've stumbled upon a monster's lair during their feast..."
        ]
        
    def generate_battle(self) -> Dict:
        """Generate a random battle scenario"""
        setting = random.choice(self.settings)
        storyline = random.choice(self.storylines)
        
        # Generate 1-3 random monsters
        num_monsters = random.randint(1, 3)
        monsters = []
        for _ in range(num_monsters):
            template = random.choice(self.monster_templates)
            monster = Monster(
                template["name"],
                template["hp"],
                template["attack"],
                template["defense"]
            )
            monsters.append(monster)
            
        return {
            "setting": setting,
            "storyline": storyline,
            "monsters": monsters
        }
        
    def calculate_damage(self, attack: int, defense: int) -> int:
        """Calculate damage dealt based on attack and defense stats"""
        base_damage = max(0, attack - defense)
        variance = random.uniform(0.8, 1.2)
        return int(base_damage * variance)