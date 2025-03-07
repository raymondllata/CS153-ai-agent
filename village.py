from typing import Dict, List
import random
from user import User
import os
import asyncio
import time

class Village:
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

        self.shop_items = {}  # Will be populated by API call
        self.special_items = {}  # Keep special items for now

        '''
        # Base shop items - should be replaced with API calls
        self.shop_items = {
            "Health Potion": {"price": 50, "heal": 30, "description": "Restores 30 HP"},
            "Super Potion": {"price": 100, "heal": 70, "description": "Restores 70 HP"},
            "Strength Elixir": {"price": 80, "stat_boost": {"Strength": 2}, "description": "Temporarily boosts Strength by 2"},
            "Wisdom Scroll": {"price": 80, "stat_boost": {"Wisdom": 2}, "description": "Temporarily boosts Wisdom by 2"},
            "Iron Sword": {"price": 150, "attack": 10, "description": "Increases Attack by 10"},
            "Steel Shield": {"price": 120, "defense": 8, "description": "Increases Defense by 8"}
        }
        
        # Special items that may appear based on stats - should be replaced with API calls
        self.special_items = {
            "Intelligence": {
                "Arcane Tome": {"price": 200, "stat_boost": {"Intelligence": 3, "Wisdom": 1}, "min_stat": 14},
                "Staff of Power": {"price": 300, "attack": 15, "stat_boost": {"Intelligence": 2}, "min_stat": 16}
            },
            "Charisma": {
                "Noble's Cloak": {"price": 180, "defense": 5, "stat_boost": {"Charisma": 2}, "min_stat": 14},
                "Diplomatic Seal": {"price": 250, "stat_boost": {"Charisma": 3}, "min_stat": 16}
            },
            "Wisdom": {
                "Holy Symbol": {"price": 220, "heal": 50, "stat_boost": {"Wisdom": 2}, "min_stat": 14},
                "Prophet's Staff": {"price": 280, "attack": 12, "stat_boost": {"Wisdom": 3}, "min_stat": 16}
            }
        }'''
    
    async def refresh_shop_items(self, story_info=None):
        """Refresh shop inventory using the Mistral API"""
        self.shop_items = {}
        try:
            items_data = await self.agent.generate_village_items(
                existing_items=self.shop_items,
                story_info=story_info
            )
            # Convert API response format to our shop format
            new_shop_items = {}
            for item in items_data["items"]:
                item_stats = {}
                
                # Set price
                item_stats["price"] = item["price"]
                item_stats["description"] = item["description"]
                
                # Add stats based on item type
                if item["type"] == "Weapon":
                    item_stats["attack"] = random.randint(5, 15)
                elif item["type"] == "Armor":
                    item_stats["defense"] = random.randint(3, 10)
                elif item["type"] == "Potion":
                    item_stats["heal"] = random.randint(20, 50)
                elif item["type"] == "Magical":
                    # Random stat boost
                    stat = random.choice(["Strength", "Wisdom", "Intelligence", "Charisma"])
                    item_stats["stat_boost"] = {stat: random.randint(1, 3)}
                
                new_shop_items[item["name"]] = item_stats
            
            self.shop_items = new_shop_items
            return True
        except Exception as e:
            print(f"Error refreshing shop items: {e}")
            # Fallback to some basic items if API fails
            self.shop_items = {
                "Health Potion": {"price": 50, "heal": 30, "description": "Restores 30 HP"},
                "Iron Sword": {"price": 150, "attack": 10, "description": "Increases Attack by 10"}
            }
            return False

    def calculate_price_modifier(self, user: User) -> float:
        """Calculate price modifier based on Charisma"""
        # Base discount is 1% per point of Charisma above 10
        charisma_discount = max(0, (user.stats["Charisma"] - 10) * 0.01)
        
        # Additional discount based on level (0.5% per level)
        level_discount = user.level * 0.005
        
        # Total discount capped at 30%
        total_discount = min(0.30, charisma_discount + level_discount)
        return 1 - total_discount

    def calculate_healing_modifier(self, user: User) -> float:
        """Calculate healing effectiveness based on Wisdom"""
        # Base healing bonus is 2% per point of Wisdom above 10
        wisdom_bonus = max(0, (user.stats["Wisdom"] - 10) * 0.02)
        
        # Additional bonus based on level (1% per level)
        level_bonus = user.level * 0.01
        
        # Total bonus capped at 50%
        total_bonus = min(0.50, wisdom_bonus + level_bonus)
        return 1 + total_bonus

    def get_available_items(self, user: User) -> Dict:
        """Get available items based on user's stats"""
        available_items = self.shop_items.copy()
        
        # Check each stat for special items
        for stat, items in self.special_items.items():
            if user.stats[stat] >= 14:  # Minimum stat threshold for special items
                for item_name, item_data in items.items():
                    if user.stats[stat] >= item_data["min_stat"]:
                        available_items[item_name] = item_data
        
        return available_items

    def heal_player(self, user: User, combat_stats: Dict, amount: int) -> Dict:
        """
        Heal the player for the specified amount, applying Wisdom bonuses
        Returns dict with success status and messages
        """
        if combat_stats["current_hp"] >= combat_stats["max_hp"]:
            return {"success": False, "message": "Already at full health!"}
            
        # Calculate actual healing needed
        healing_needed = min(amount, combat_stats["max_hp"] - combat_stats["current_hp"])
        
        # Apply Wisdom bonus to healing
        healing_modifier = self.calculate_healing_modifier(user)
        actual_healing = int(healing_needed * healing_modifier)
        
        # Calculate cost (reduced by Charisma)
        base_cost = healing_needed + 10  # Base healing cost plus service fee
        price_modifier = self.calculate_price_modifier(user)
        final_cost = int(base_cost * price_modifier)
        
        if combat_stats["coins"] < final_cost:
            return {
                "success": False, 
                "message": f"Not enough coins! Healing would cost {final_cost} coins."
            }
            
        # Apply healing and deduct cost
        combat_stats["coins"] -= final_cost
        combat_stats["current_hp"] += actual_healing
        
        # Ensure we don't exceed max HP
        combat_stats["current_hp"] = min(combat_stats["current_hp"], combat_stats["max_hp"])
        
        return {
            "success": True,
            "message": (f"Healed for {actual_healing} HP! (Wisdom bonus: +{int(healing_modifier*100-100)}%)\n"
                       f"Cost: {final_cost} coins (Charisma discount: {int((1-price_modifier)*100)}%)")
        }

    def buy_item(self, user: User, combat_stats: Dict, item_name: str) -> Dict:
        """
        Attempt to buy an item
        Returns dict with success status and messages
        """
        available_items = self.get_available_items(user)
        if item_name not in available_items:
            return {"success": False, "message": "Item not available!"}
            
        item = available_items[item_name]
        
        # Apply Charisma discount
        price_modifier = self.calculate_price_modifier(user)
        final_price = int(item["price"] * price_modifier)
        
        if combat_stats["coins"] < final_price:
            return {"success": False, "message": f"Not enough coins! {item_name} costs {final_price} coins."}
            
        # Process purchase
        combat_stats["coins"] -= final_price
        user.add_item(item_name)
        
        # Apply immediate effects
        effects_message = []
        if "heal" in item:
            healing = self.heal_player(user, combat_stats, item["heal"])
            effects_message.append(healing["message"])
        if "attack" in item:
            combat_stats["attack"] += item["attack"]
            effects_message.append(f"Attack increased by {item['attack']}")
        if "defense" in item:
            combat_stats["defense"] += item["defense"]
            effects_message.append(f"Defense increased by {item['defense']}")
            
        return {
            "success": True,
            "message": (f"Bought {item_name} for {final_price} coins "
                       f"(Charisma discount: {int((1-price_modifier)*100)}%)\n"
                       f"Effects: {', '.join(effects_message)}")
        }