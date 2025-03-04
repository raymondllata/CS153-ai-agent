from typing import List, Dict
import random
import requests
import os
from dotenv import load_dotenv

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
        # Load API configuration
        load_dotenv()  # Load environment variables
        self.api_key = os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
            
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        
        # Placeholder monsters that could be replaced with API calls
        self.monster_templates = [
             {"name": "Goblin", "hp": 20, "attack": 5, "defense": 2},
             {"name": "Orc", "hp": 35, "attack": 8, "defense": 4},
             {"name": "Dragon", "hp": 100, "attack": 15, "defense": 8}
         ]
        
        # Settings and storylines that could be generated via API as well
        self.settings = [
            "Dark Forest",
            "Ancient Ruins",
            "Volcanic Cave",
            "Haunted Castle"
        ]
        
        self.storylines = [
            "A mysterious fog surrounds you as creatures emerge from the shadows...",
            "The ancient guardian awakens, protecting its sacred grounds...",
            "You've stumbled upon a monster's lair during their feast..."
        ]

    def generate_monster_template(self) -> Dict:
        """Generate a monster template using the Mistral API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = """Generate a fantasy monster with the following attributes. Be imaginative. Return only a JSON object with no other text:
            {
                "name": "unique monster name",
                "hp": number between 20-150,
                "attack": number between 5-20,
                "defense": number between 2-12
            }"""

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "model": "mistral-tiny",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            import json
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Error generating monster: {e}")
            return {
                random.choice(self.monster_templates)
            }

    def generate_battle(self) -> Dict:
        """Generate a random battle scenario"""
        setting = random.choice(self.settings)
        storyline = random.choice(self.storylines)
        
        # Generate 1-3 random monsters using the API
        num_monsters = random.randint(1, 3)
        monsters = []
        for _ in range(num_monsters):
            # template = random.choice(self.monster_templates)
            template = self.generate_monster_template()
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