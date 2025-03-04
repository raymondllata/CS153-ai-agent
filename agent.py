import os
from mistralai import Mistral
import discord
import json
import random
from typing import Dict

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = "You are a Dungeions and Dragons game teller. You will answer like so. Be creative and have fun! Do not repeat stories."


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
            