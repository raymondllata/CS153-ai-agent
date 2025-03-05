import os
from mistralai import Mistral
import discord
import json
import random
import time
import asyncio
from typing import Dict
import re

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = "You are a Dungeons and Dragons game teller. Be creative and have fun! Do not repeat stories. You should be amenable to user's prompts (the first line of every request). The story should try to adhere to the themes of the user stated theme, even if not necessairly a D&D theme. Be creative."


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)
        print("Mistral client initialized")
        
        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 1.5  # Minimum 1 second between requests



    async def rate_limit(self):
        """Ensure we don't exceed rate limits by waiting if needed; Rate Limiting Parameters established on INIT"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            # Calculate how much longer we need to wait
            wait_time = self.min_request_interval - time_since_last_request
            print(f"Rate limiting: Waiting {wait_time:.2f} seconds before next API call")
            await asyncio.sleep(wait_time)
        
        # Update the last request time
        self.last_request_time = time.time()

    """
    This is the default method for the MistralAgent class. It sends a message to the Mistral API and returns the response.
    Not used for our project."""
    async def run(self, message: discord.Message):
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        try:
            # The simplest form of an agent
            # Send the message's content to Mistral's API and return Mistral's response
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.content},
            ]

            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in run method: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again."

    async def generate_monster_template(self, existing_templates, story_info) -> Dict:
        """Generate a monster template using the Mistral API with rate limiting
        This function passes prior information of existing monster templates and prior story information to the API"""
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        prompt = """Generate a fantasy monster with the following attributes. Be imaginative. Return only a JSON string object with no other text in the following format:
            {
                "name": "unique monster name relevant to the story",
                "hp": number between 20-150,
                "attack": number between 5-20,
                "defense": number between 2-12
            }.
            
            Only return a JSON string object. Should not contain any other text. Please only return a JSON string formatted object.
             
              
               Do not repeat any monsters that have already been created. """
        
        prompt += "\n" + "Existing Monsters: " + str(existing_templates) + "\n" + "Story Info: " + str(story_info) 
        prompt += "\n" + "If possible, generate a monster/person that makes sense for the given story_information and existing monsters."
        
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )
            
            # Access the content directly from the response object
            content = response.choices[0].message.content
            print(f"Monster template response: {content[:100]}...")  # Print first 100 chars to avoid flooding console

            # Parse the JSON string contained in the response content
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")
            # Fallback to a default monster if parsing fails
            return {
                "name": f"Mystery Creature {random.randint(1, 100)}",
                "hp": random.randint(20, 100),
                "attack": random.randint(5, 15),
                "defense": random.randint(2, 8)
            }
        except Exception as e:
            print(f"Error generating monster: {e}")
            return None
    
    async def estimate_attack_damage(self, user_attack: str) -> int:
        """Estimate the damage done (3-10) based on user attack input using the Mistral API"""
        await self.rate_limit()  # Ensure rate limiting is applied

        prompt = f"""Rate the effectiveness of the following attack on a scale from 3 to 10 based on its power, technique, and potential damage. Respond with only a JSON object in this format:
        {{
            "damage_score": number between 3-10
        }}

        Attack description: "{user_attack}" 
        """

        try:
            messages = [
                {"role": "system", "content": "You are a combat AI that rates attack effectiveness from 3 to 10 based on power, technique, and impact."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat.complete_async(
                model="mistral-medium",
                messages=messages,
            )

            # Extract response content
            content = response.choices[0].message.content.strip()

            # 🛠 FIX 1: Remove Markdown formatting like ```json ```
            if content.startswith("```json"):
                content = content[7:-3].strip()  # Remove ```json and trailing ```
            elif content.startswith("```"):
                content = content[3:-3].strip()  # Remove ``` and trailing ```

            # 🛠 FIX 2: Remove invalid backslashes before parsing
            content = re.sub(r"\\_", "_", content)  # Fix incorrect `\_` escape sequences

            print(f"User attack input: {user_attack}")
            print(f"Attack damage response (cleaned): {content}")  # Debugging print

            # 🛠 FIX 3: Handle empty response
            if not content:
                print("Warning: Empty API response!")
                return random.randint(3, 10)  # Fallback to a random score

            # Parse JSON response
            damage_data = json.loads(content)

            # Ensure damage is within 3-10 range
            score = max(3, min(10, damage_data.get("damage_score", 3)))  # Ensures minimum of 3
            return score * random.uniform(1, 3)

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")  # Show actual response
            return random.randint(3, 10)  # Fallback to a random score

        except Exception as e:
            print(f"Error estimating attack damage: {e}")
            return -1  # Indicate an error occurred
    
    "Generates a story segment using Mistral's API; called on entry to a battle. This function passes prior story information to the API, and the current Battle Class State to the API"
    async def generate_story(self, story_info, battle_info: dict):
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        try:
            # Generate a story prompt using Mistral's API
            content = "Previous Stories: " + str(story_info) + "\n" + "Battle Info: " + str(battle_info) + "\n" + "Generate a story prompt that makes sense for the given battle_information and previous stories. Keep your response concise and engaging. Less then 100 words. The story should begin where the last story left off, and connect them accordingly"

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]

            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )
            
            story_info.append(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating story: {e}")
            fallback_story = "As you continue your journey, you encounter new challenges..."
            story_info.append(fallback_story)
            return fallback_story
    
    """
    Generates a theme header using Mistral's API; called on entry to a new story
    This function is needed to emphasize the theme element of the story, otherwise the AI tends to ignore it
    Passes in the prior story information to the API"""
    async def generate_theme_header(self, story_info):
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        try:
            # Generate a theme header using Mistral's API
            content = "Previous Stories: " + str(story_info) + "\n" + "Generate a theme header that makes sense for the given story_information. Keep your response concise and engaging. Less then 100 words. The theme should be related to the story prompt."

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]

            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )

            story_info.append(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating theme header: {e}")
            fallback_header = "The Adventure Continues..."
            story_info.append(fallback_header)
            return fallback_header
    

    # Generate a conclusion using Mistral's API
    # pass in relevant story information
    async def generate_end_message(self, story_info):
        # Apply rate limiting before making the API call
        await self.rate_limit()
        
        try:
            # Generate a conclusion using Mistral's API
            content = "Previous Stories: " + str(story_info) + "\n" + "Generate a conclusion that makes sense for the given story_information. Keep your response concise and engaging. Less then 100 words. The conclusion should wrap up the story and leave room for future stories."

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]

            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )

            story_info.append(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating end message: {e}")
            fallback_end = "Your adventure concludes for now, but new challenges await on the horizon..."
            story_info.append(fallback_end)
            return fallback_end