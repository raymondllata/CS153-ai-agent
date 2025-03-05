from typing import List, Dict
import random
import os
import asyncio
import time

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
    def __init__(self, agent=None):
        # Load API configuration
        self.api_key = os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
            
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.agent = agent
        
        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
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

    async def rate_limit(self):
        """Ensure we don't exceed rate limits by waiting if needed"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            # Calculate how much longer we need to wait
            wait_time = self.min_request_interval - time_since_last_request
            print(f"Rate limiting: Waiting {wait_time:.2f} seconds before next API call")
            await asyncio.sleep(wait_time)
        
        # Update the last request time
        self.last_request_time = time.time()

    async def get_new_monster_template(self, story_info):
        """Get a new monster template with rate limiting"""
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        if self.agent:
            try:
                template = await self.agent.generate_monster_template(self.monster_templates, story_info)
                if template:
                    print(f"Generated new monster: {template['name']}")
                    return template
            except Exception as e:
                print(f"Error in monster generation: {e}")
        
        # Fallback to a random existing template if API call fails
        return random.choice(self.monster_templates)

    async def generate_battle(self, story_info) -> Dict:
        """Generate a random battle scenario"""
        setting = random.choice(self.settings)
        storyline = random.choice(self.storylines)
        
        # First, ensure we have enough templates (at least 7)
        if self.agent and len(self.monster_templates) < 7:
            print(f"Currently have {len(self.monster_templates)} monster templates, generating more...")
            while len(self.monster_templates) < 7:
                template = await self.get_new_monster_template(story_info)
                if template not in self.monster_templates:  # Avoid duplicates
                    self.monster_templates.append(template)
        
        # Generate 1-3 random monsters for the battle
        num_monsters = random.randint(1, 3)
        monsters = []
        
        # Add a new template once per battle for variety
        if self.agent:
            new_template = await self.get_new_monster_template(story_info)
            if new_template not in self.monster_templates:
                self.monster_templates.append(new_template)
        
        # Select random monsters from our templates
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
        return min(1, int(base_damage * variance))