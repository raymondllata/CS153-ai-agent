import os
import discord
import json
import logging

from discord.ext import commands
from dotenv import load_dotenv
from agent import MistralAgent
from battle import Battle
from village import Village
from start_story import StorySystem
from user import get_user
from user import load_users

PREFIX = "!"
STORY_STARTED = False

# Setup logging
logger = logging.getLogger("discord")

# Load the environment variables
load_dotenv()

# Create the bot with all intents
# The message content and members intent must be enabled in the Discord Developer Portal for the bot to work.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Import the Mistral agent from the agent.py file
agent = MistralAgent()

# Get the token from the environment variables
token = os.getenv("DISCORD_TOKEN")


@bot.event
async def on_ready():
    """
    Called when the client is done preparing the data received from Discord.
    Prints message on terminal when bot successfully connects to discord.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_ready
    """
    logger.info(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in any channel the bot can see.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    """
    # Don't delete this line! It's necessary for the bot to process commands.
    await bot.process_commands(message)

    # Ignore messages from self or other bots to prevent infinite loops.
    if message.author.bot or message.content.startswith("!"):
        return
    
    # Check if bot is paused before making API calls
    if STORY_STARTED:
        return

    # Process the message with the agent you wrote
    # Open up the agent.py file to customize the agent
    logger.info(f"Processing message from {message.author}: {message.content}")
    response = await agent.run(message)

    # Split response into chunks of 2000 characters or less
    # Use a helper function to split on sentence boundaries when possible
    def split_into_chunks(text, chunk_size=2000):
        chunks = []
        current_chunk = ""
        
        # Split text into sentences (roughly)
        sentences = text.replace('\n', '\n.').split('.')
        
        for sentence in sentences:
            # Add the period back unless it's a newline
            if not sentence.strip().endswith('\n'):
                sentence = sentence + '.'
                
            # If adding this sentence would exceed chunk size, start a new chunk
            if len(current_chunk) + len(sentence) > chunk_size:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
                
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    # Send each chunk as a separate message
    chunks = split_into_chunks(response)
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk uses reply to maintain threading
            await message.reply(chunk)
        else:
            # Subsequent chunks use regular send
            await message.channel.send(chunk)


# Commands


# This example command is here to show you how to add commands to the bot.
# Run !ping with any number of arguments to see the command in action.
# Feel free to delete this if your project will not need commands.
@bot.command(name="ping", help="Pings the bot.")
async def ping(ctx, *, arg=None):
    if arg is None:
        await ctx.send("Pong!")
    else:
        await ctx.send(f"Pong! Your argument was {arg}")

@bot.command(name="start", help="Starts the game")
async def start(ctx, *, arg=None):
    global STORY_STARTED
    STORY_STARTED = True
    story = StorySystem()
    if arg is None:
        await ctx.send("Starting the game...")
    else:
        await ctx.send(f"Starting the game... {arg}")
    # Start the adventure
    try:
        await story.start_adventure(ctx)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name="village", help="Tests Village")
async def village(ctx, *, arg=None):
    global STORY_STARTED
    STORY_STARTED = True
    story = StorySystem()
    if arg is None:
        await ctx.send("Starting the village test...")
    else:
        await ctx.send(f"Starting the village tst... {arg}")
    # Start the adventure
    try:
        await story.test_village(ctx)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    
# This command prints all existing users
# @bot.command(name="show_users", help="Prints all stored users.")
# async def show_users(ctx):
#     users = load_users()
#     await ctx.send(f"```json\n{json.dumps(users, indent=4)}```")

# Makes the bot stop
@bot.command(name="quit", help="Shuts down the bot.")
async def quit(ctx):
    """Safely shuts down the bot"""
    await ctx.send("Shutting down... Goodbye!")
    await bot.close()



# Start the bot, connecting it to the gateway
bot.run(token)
