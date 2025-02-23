from typing import Dict
import random
from battle import Battle, Monster
from village import Village
from user import User, make_random_user
import asyncio

class StorySystem:
    def __init__(self):
        self.battle_system = Battle()
        self.village = Village()
        self.base_end_probability = 0.1  # Starting 10% chance to end
        self.current_end_probability = self.base_end_probability
        self.force_end = False
        
        # Class-based stat modifiers
        self.class_modifiers = {
            "Warrior": {"Strength": 2, "Constitution": 2, "Dexterity": 1},
            "Mage": {"Intelligence": 3, "Wisdom": 2, "Constitution": -1},
            "Rogue": {"Dexterity": 3, "Charisma": 1, "Constitution": 1},
            "Cleric": {"Wisdom": 2, "Charisma": 2, "Intelligence": 1}
        }
    
    def should_end_story(self) -> bool:
        """Determine if the story should end based on current probability"""
        should_end = random.random() < self.current_end_probability
        if not should_end:
            # Double the probability for next time
            self.current_end_probability *= 2
        return should_end

    def reset_end_probability(self):
        """Reset the end probability to base value"""
        self.current_end_probability = self.base_end_probability

    def calculate_combat_stats(self, user: User) -> Dict:
        """Calculate combat stats based on user's level and class"""
        base_stats = {
            "max_hp": 50 + (user.stats["Constitution"] * 5) + (user.level * 10),
            "current_hp": 50 + (user.stats["Constitution"] * 5) + (user.level * 10),
            "attack": 10 + (user.stats["Strength"] * 2) + (user.level * 3),
            "defense": 5 + (user.stats["Constitution"] * 1.5) + (user.level * 2),
            "coins": 100 + (user.level * 50)
        }
        
        # Apply class modifiers
        if user.character_class in self.class_modifiers:
            mods = self.class_modifiers[user.character_class]
            for stat, mod in mods.items():
                if stat == "Constitution":
                    base_stats["max_hp"] += mod * 10
                    base_stats["current_hp"] += mod * 10
                elif stat == "Strength":
                    base_stats["attack"] += mod * 3
                elif stat == "Dexterity":
                    base_stats["defense"] += mod * 2
        
        return base_stats

    async def start_adventure(self, ctx) -> None:
        """Main story flow with repeating adventures"""
        # Get or create user
        user = make_random_user()
        combat_stats = self.calculate_combat_stats(user)
        
        # Initial message
        await ctx.send(f"Welcome {user.name}, Level {user.level} {user.character_class}!")
        await ctx.send(user.show_stats())
        
        # Reset probability at start of new adventure
        self.reset_end_probability()
        
        while True:  # Infinite loop for continuing adventures
            await ctx.send(f"\nCurrent Stats: HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}, "
                         f"Attack: {combat_stats['attack']}, Defense: {combat_stats['defense']}, "
                         f"Coins: {combat_stats['coins']}")
            
            if self.force_end:
                await ctx.send(f"\n{user.name}'s adventure is cut short by fate...")
                await ctx.send(f"Final Level: {user.level}")
                await ctx.send(f"Final Coins: {combat_stats['coins']}")
                break

            # Check if story should end
            if self.should_end_story():
                await ctx.send(f"\nAfter many adventures, {user.name} decides to retire...")
                await ctx.send(f"Final Level: {user.level}")
                await ctx.send(f"Final Coins: {combat_stats['coins']}")
                break
            
            # Generate and start battle
            survived = await self.run_battle(ctx, user, combat_stats)
            
            if not survived:
                await ctx.send(f"{user.name}'s journey comes to an end...")
                break
            
            # After battle, visit village if survived
            await self.visit_village(ctx, user, combat_stats)
            
            # Check for level up conditions
            if random.random() < 0.3:  # 30% chance to level up
                level_message = user.level_up()
                await ctx.send(level_message)
                
                # Recalculate combat stats after leveling up
                new_stats = self.calculate_combat_stats(user)
                await ctx.send(level_message)
                combat_stats['max_hp'] = new_stats['max_hp']
                await ctx.send(level_message)
                combat_stats['attack'] = new_stats['attack']
                combat_stats['defense'] = new_stats['defense']
                await ctx.send(level_message)
                # Save updated user data
                # users = load_users()
                await ctx.send(level_message)
                #users[str(user.user_id)]["level"] = user.level
                # save_users(users)
            
            await ctx.send("\nYour adventure continues...")

    async def test_village(self, ctx) -> None:
        # Get or create user
        # user = get_user(ctx.author.id)
        user = make_random_user()
        combat_stats = self.calculate_combat_stats(user)
        
        # Initial message
        await ctx.send(f"Welcome {user.name}, Level {user.level} {user.character_class}!")
        await ctx.send(user.show_stats())
        await ctx.send(f"Combat Stats: HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}, "
                      f"Attack: {combat_stats['attack']}, Defense: {combat_stats['defense']}, "
                      f"Coins: {combat_stats['coins']}")
        survived = True
        
        # After battle, visit village if survived
        if survived:
            await self.visit_village(ctx, user, combat_stats)
            
            # Check for level up conditions (simplified)
            if random.random() < 0.3:  # 30% chance to level up after successful adventure
                level_message = user.level_up()
                await ctx.send(level_message)
                
                # Save updated user data
                # users = load_users()
                # users[str(user.user_id)]["level"] = user.level
                # save_users(users)
    
    async def run_battle(self, ctx, user: User, combat_stats: Dict) -> bool:
        """Handle battle sequence, returns True if player survives"""
        battle = self.battle_system.generate_battle()
        
        # API CALL: Send battle data (ie. setting, monsters, current user) to Mistral, and generate a story line to print out
        await ctx.send(f"\n{battle['storyline']}")
        await ctx.send(f"Location: {battle['setting']}")
        
        enemy_list = ""
        for monster in battle['monsters']:
            enemy_list += f"- {monster.name} (HP: {monster.current_hp})\n"
        await ctx.send(f"You encounter:\n{enemy_list}")
        
        # Battle loop
        while any(monster.is_alive() for monster in battle['monsters']) and combat_stats['current_hp'] > 0:
            # Player's turn
            for monster in battle['monsters']:
                if monster.is_alive():
                    damage = self.battle_system.calculate_damage(combat_stats['attack'], monster.defense)
                    monster.current_hp -= damage
                    await ctx.send(f"{user.name} attacks {monster.name} for {damage} damage!")
                    
                    if not monster.is_alive():
                        await ctx.send(f"{monster.name} has been defeated!")
                        
                        # Add random loot
                        loot = random.choice(["Health Potion", "Strength Elixir", "Defense Charm"])
                        loot_message = user.add_item(loot)
                        await ctx.send(loot_message)
                        
                        combat_stats['coins'] += random.randint(20, 50)
            
            # Monsters' turn
            for monster in battle['monsters']:
                if monster.is_alive():
                    damage = self.battle_system.calculate_damage(monster.attack, combat_stats['defense'])
                    combat_stats['current_hp'] -= damage
                    await ctx.send(f"{monster.name} attacks {user.name} for {damage} damage!")
                    
                    if combat_stats['current_hp'] <= 0:
                        await ctx.send(f"{user.name} has been defeated!")
                        return False
        
        if combat_stats['current_hp'] > 0:
            await ctx.send(f"Victory! You survived with {combat_stats['current_hp']} HP remaining!")
            await ctx.send(f"You now have {combat_stats['coins']} coins!")
            return True
        return False
    
    async def visit_village(self, ctx, user: User, combat_stats: Dict) -> None:
        """Handle village sequence with user interaction"""
        await ctx.send("\nYou arrive at the village to rest and recover...")
        
        while True:  # Keep running until user chooses to leave
            # Display current stats
            await ctx.send(f"\nCurrent HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}")
            await ctx.send(f"Coins: {combat_stats['coins']}")
            
            options_message = """
            What would you like to do?
            1️⃣ Visit the healer (1 HP = 1 coin + 10 coin fee)
            2️⃣ Visit the shop
            3️⃣ Leave village
            """
            await ctx.send(options_message)
            
            try:
                # Wait for user response
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                
                response = await ctx.bot.wait_for('message', timeout=30.0, check=check)
                
                # Process user choice
                choice = response.content.lower()
                
                if choice in ['1', 'healer', 'visit healer']:
                    healing_needed = combat_stats['max_hp'] - combat_stats['current_hp']
                    healing_cost = healing_needed + 10  # Base cost + service fee
                    
                    if combat_stats['coins'] >= healing_cost:
                        combat_stats['coins'] -= healing_cost
                        combat_stats['current_hp'] = combat_stats['max_hp']
                        await ctx.send(f"You've been healed to full health! Current HP: {combat_stats['current_hp']}")
                        await ctx.send(f"Remaining coins: {combat_stats['coins']}")
                    else:
                        await ctx.send("Not enough coins for healing!")
                
                elif choice in ['2', 'shop', 'visit shop']:
                    # Show shop inventory
                    shop_message = "Available items in shop:"
                    for item, details in self.village.shop_items.items():
                        shop_message += f"\n- {item}: {details['price']} coins"
                    await ctx.send(shop_message)
                    
                    # Wait for shop choice
                    await ctx.send("What would you like to buy? (Type the item name or 'back' to return)")
                    shop_response = await ctx.bot.wait_for('message', timeout=30.0, check=check)
                    
                    if shop_response.content.lower() != 'back':
                        # Try to buy the item
                        result = self.village.buy_item(user, combat_stats, shop_response.content)
                        await ctx.send(result['message'])
                
                elif choice in ['3', 'leave', 'leave village']:
                    await ctx.send("You leave the village and continue your journey...")
                    break
                
                else:
                    await ctx.send("Invalid choice! Please select 1, 2, or 3.")
            
            except asyncio.TimeoutError:
                await ctx.send("No response received. Please make a selection!")
                continue

# Mock Discord context for terminal testing
class MockContext:
    def __init__(self, user_id=12345, username="TestUser"):
        self.author = type('MockAuthor', (), {'id': user_id, 'name': username})
        
    async def send(self, message):
        print(message)
        
    async def reply(self, message):
        print(f"Reply: {message}")

# Main execution for terminal testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create mock context and story
        mock_ctx = MockContext(user_id=12345, username="TerminalUser")
        story = StorySystem()
        
        # Run the adventure
        await story.start_adventure(mock_ctx)
    
    # Run the async main function
    asyncio.run(main())