from typing import Dict
import random
from battle import Battle, Monster
from village import Village
from user import User, make_random_user, parse_character_json
import asyncio
import re

class StorySystem:
    def __init__(self, agent = None):
        self.agent = agent
        self.battle_system = Battle(agent=self.agent)
        self.village = Village()
        self.base_end_probability = 0.1  # Starting 10% chance to end
        self.current_end_probability = self.base_end_probability
        self.force_end = False
        self.agent = agent
        
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

    async def start_adventure(self, ctx, story_info=None) -> None:
        """Main story flow with repeating adventures"""
        # Get or create user
        # Ask the user what kind of adventurer they want to be
        await ctx.send("Welcome to the adventure! What kind of character would you like to be? Describe your ideal adventurer (class, background, etc.) Press Enter to skip:")
        
        def check(message):
            # Check if the message is from the user who initiated the command
            return message.author == ctx.author
        
        try:
            # Wait for player's response with a 120-second timeout
            player_response = await ctx.bot.wait_for('message', check=check, timeout=120.0)
            
            # Append the user's preference to story_info for context
            user_preference = player_response.content

            if len(user_preference) < 2:
                user = make_random_user()

            else:
            # story_info.append(f"Player wants to be: {user_preference}")
            
                await ctx.send("Creating your character... Please wait a moment.")
                
                # Generate character based on player's preference using Mistral API
                character_json = await self.agent.generate_character(story_info, user_preference)
                
                # Parse the JSON into a User object
                user = parse_character_json(character_json)
                
                # Calculate combat stats based on the created character
                combat_stats = self.calculate_combat_stats(user)
            
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond! Creating a random character for you.")
            user = make_random_user()
            combat_stats = self.calculate_combat_stats(user)
        
        # Initial message with character info
        if hasattr(user, 'background'):
            await ctx.send(f"Welcome {user.name}, Level {user.level} {user.character_class}!")
            await ctx.send(f"Background: {user.background}")
        else:
            await ctx.send(f"Welcome {user.name}, Level {user.level} {user.character_class}!")
        
        await ctx.send(user.show_stats())
        await ctx.send(f"Combat Stats: HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}, "
                    f"Attack: {combat_stats['attack']}, Defense: {combat_stats['defense']}, "
                    f"Coins: {combat_stats['coins']}")
        combat_stats = self.calculate_combat_stats(user)

        # Generate story details if needed
        if story_info == [] or story_info is None:
            story_info = [user.name + " the " + user.character_class + " is on a crazy adventure!"] 
        
        # Initial message
        await ctx.send(f"Welcome {user.name}, Level {user.level} {user.character_class}!")
        # await ctx.send(user.show_stats())
        
        # Reset probability at start of new adventure
        self.reset_end_probability()
        round = 0
        
        while True:  # Infinite loop for continuing adventures
            # await ctx.send(f"\nCurrent Stats: HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}, "
            #              f"Attack: {combat_stats['attack']}, Defense: {combat_stats['defense']}, "
            #              f"Coins: {combat_stats['coins']}")
            round += 1
            if self.force_end or (self.should_end_story() and round > 3):
                end_message = await self.agent.generate_end_message(story_info)
                await ctx.send(end_message)
                #await ctx.send(f"\n{user.name}'s adventure is cut short by fate...")
                await ctx.send(f"Final Level: {user.level}")
                await ctx.send(f"Final Coins: {combat_stats['coins']}")
                break

            # # Check if story should end
            # if self.should_end_story() or self.force_end:
            #     end_message = self.agent.generate_end_message()
            #     await ctx.send(end_message)
            #     #await ctx.send(f"\nAfter many adventures, {user.name} decides to retire...")
            #     await ctx.send(f"Final Level: {user.level}")
            #     await ctx.send(f"Final Coins: {combat_stats['coins']}")
            #     break
            
            # Generate and start battle
            survived = await self.run_battle(ctx, user, combat_stats, story_info)
            
            if not survived:
                await ctx.send(f"{user.name}'s journey comes to an end...")
                break
            
            # After battle, 30% chance to visit village if survived
            await self.visit_village(ctx, user, combat_stats)
            
            # Check for level up conditions
            if random.random() < 0.3:  # 30% chance to level up
                level_message = user.level_up()
                # await ctx.send(level_message)
                
                # Recalculate combat stats after leveling up
                new_stats = self.calculate_combat_stats(user)
                # await ctx.send(level_message)
                combat_stats['max_hp'] = new_stats['max_hp']
                # await ctx.send(level_message)
                combat_stats['attack'] = new_stats['attack']
                combat_stats['defense'] = new_stats['defense']
                # await ctx.send(level_message)
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
    
    async def run_battle(self, ctx, user: User, combat_stats: Dict, story_info = None) -> bool:
        """Handle battle sequence, returns True if player survives"""
        print("Generating Battle...")
        battle = await self.battle_system.generate_battle(story_info=story_info)
        print("Done Generating Battle")

        await asyncio.sleep(1) # 1 Request per second delay
        
        # API CALL: Send battle data (ie. setting, monsters, current user) to Mistral, and generate a story line to print out
        if self.agent != None:
            print("Generating Story...")
            mistral_story = await self.agent.generate_story(story_info, battle)
            await ctx.send(f"\n{mistral_story}")
        else:
            await ctx.send(f"\n{battle['storyline']}")
            await ctx.send(f"Location: {battle['setting']}")
        
        # Battle loop
        count = 0
        while any(monster.is_alive() for monster in battle['monsters']) and combat_stats['current_hp'] > 0:
            # Display current monster status
            count += 1
            alive_monsters = [monster for monster in battle['monsters'] if monster.is_alive()]
            
            enemy_list = ""
            for i, monster in enumerate(alive_monsters, 1):
                enemy_list += f"{i}. {monster.name} (HP: {monster.current_hp})\n"
            
            await ctx.send(f"Current enemies:\n{enemy_list}")
            await ctx.send(f"Your HP: {combat_stats['current_hp']}/{combat_stats['max_hp']}")
            
            # Ask player which monster to attack
            await ctx.send("Which monster do you want to attack? (Enter the number followed by a space and any attack details)")
            
            def check(message):
                # Check if the message is from the user and starts with a number
                return message.author == ctx.author and message.content.strip()[0].isdigit()
            
            try:
                # Wait for player's response with a 60-second timeout
                player_choice = await ctx.bot.wait_for('message', check=check, timeout=60.0)
                
                # Extract the monster number from the player's response
                monster_number = int(player_choice.content.strip()[0]) - 1
                
                # Validate the choice
                if monster_number < 0 or monster_number >= len(alive_monsters):
                    await ctx.send(f"Invalid choice! Please pick a valid number.")
                    await ctx.send("Format your answer as follows \"<Number> <Description>\" ie: \"1 Swing my Greatsword as hard as I can \"")

                    continue # repeat
                
                # Player's turn
                target_monster = alive_monsters[monster_number]
                # damage = self.battle_system.calculate_damage(combat_stats['attack'], target_monster.defense)
                damage = await self.agent.estimate_attack_damage(player_choice.content.strip()[1:]) 
                if (count > 7):
                     damage = target_monster.current_hp
                     await ctx.send(f"With a dangerous final blow, {user.name} attacks {monster.name} for {round(damage)} damage!")
                else: 
                    await ctx.send(f"{user.name} attacks {target_monster.name} for {damage} damage!")
                target_monster.current_hp -= damage
                
                if not target_monster.is_alive():
                    await ctx.send(f"{target_monster.name} has been defeated!")
                    
                    # Add random loot
                    loot = random.choice(["Health Potion", "Strength Elixir", "Defense Charm"])
                    loot_message = user.add_item(loot)
                    await ctx.send(loot_message)
                    
                    combat_stats['coins'] += random.randint(20, 50)
            
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond! Attacking the first monster by default.")
                if alive_monsters:
                    target_monster = alive_monsters[0]
                    damage = self.battle_system.calculate_damage(combat_stats['attack'], target_monster.defense)
                    target_monster.current_hp -= damage
                    await ctx.send(f"{user.name} attacks {target_monster.name} for {damage} damage!")
                    
                    if not target_monster.is_alive():
                        await ctx.send(f"{target_monster.name} has been defeated!")
                        
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
        villageProb = 0.3
        if random.random() < villageProb:
            return

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