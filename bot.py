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
# from user import get_user
# from user import load_users

PREFIX = "!"
story = None

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

    # Process the message with the agent you wrote
    # Open up the agent.py file to customize the agent
    logger.info(f"Processing message from {message.author}: {message.content}")
    response = await agent.run(message)

    # Send the response back to the channel
    await message.reply(response)


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
    global story
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

@bot.command(name="end", help="Ends the current game")
async def end(ctx):
    global story
    if story is None:
        await ctx.send("No game is currently running!")
    else:
        story.force_end = True  # Set the flag instead of probability
        await ctx.send("Ending the current game...")

@bot.command(name="village", help="Tests Village")
async def village(ctx, *, arg=None):
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


# Start the bot, connecting it to the gateway
bot.run(token)
