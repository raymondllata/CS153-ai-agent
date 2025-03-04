import os
from mistralai import Mistral
import discord
import json
import random
from typing import Dict

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = "You are a Dungeons and Dragons game teller. Be creative and have fun! Do not repeat stories. You should be amenable to user's prompts (the first line of every request). The story should try to adhere to the themes of the user stated theme, even if not necessairly a D&D theme. Be creative."


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)
        print("Mistral API Key:", MISTRAL_API_KEY)

    async def run(self, message: discord.Message):
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

    async def generate_monster_template(self) -> Dict:
        """Generate a monster template using the Mistral API"""
        # headers = {
        #     "Authorization": f"Bearer {self.api_key}",
        #     "Content-Type": "application/json"
        # }
        
        prompt = """Generate a fantasy monster with the following attributes. Be imaginative. Return only a JSON string object with no other text in the following format:
            {
                "name": "unique monster name relevant to the story",
                "hp": number between 20-150,
                "attack": number between 5-20,
                "defense": number between 2-12
            }.
            
            Only return a JSON string object. Should not contain any other text. Please only return a JSON string formatted object."""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
            ]

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        # The response is already a Python object, no need to call .json()
        # Let's print the structure to see what we're working with
        print(f"Response type: {type(response)}")
        
        # Access the content directly from the response object
        content = response.choices[0].message.content
        print(f"Content: {content}")

        try:
            # Parse the JSON string contained in the response content
            return json.loads(content)
        except Exception as e:
            print(f"Error generating monster: {e}")
            return None
    
    async def generate_story(self, story_info, battle_info: dict):
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
        print(story_info)
        story_info.append(response.choices[0].message.content)

        return response.choices[0].message.content
    
    async def generate_theme_header(self, story_info):
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
