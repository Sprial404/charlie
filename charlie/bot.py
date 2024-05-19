"""
This module contains the code for the Discord bot that will be used to count in the Discord channel.
"""

import os
import sys

import discord
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

current_count = 0
last_user_id = None

try:
    counting_channel = int(os.getenv("CHANNEL_ID"))
except ValueError:
    print("Environment variable CHANNEL_ID must be an integer.", file=sys.stderr)
    sys.exit(1)
except TypeError:
    print("Missing environment variable CHANNEL_ID.", file=sys.stderr)
    sys.exit(1)

try:
    token = os.getenv("TOKEN")
except TypeError:
    print("Missing environment variable DISCORD_BOT_TOKEN.", file=sys.stderr)
    sys.exit(1)


@client.event
async def on_ready():
    """
    This function is called when the bot is ready to start receiving events.
    """
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    """
    This function is called when a message is sent in a channel that the bot has access to.
    :param message: The message that was sent.
    """
    global current_count, last_user_id

    # Ignore messages from the bot and messages from channels that are not the counting channel.
    is_bot_message = message.author == client.user
    is_counting_channel = message.channel.id == counting_channel
    if is_bot_message or not is_counting_channel:
        return

    # Check if the message is a number.
    if message.content.isnumeric():
        try:
            value = int(message.content)
        except ValueError:
            print(
                f"Failed to convert message content to integer: {message.content}",
                file=sys.stderr,
            )
            return

        if last_user_id == message.author.id:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} **RUINED THE COUNT** at {current_count}. The next number is 1. **You can't "
                f"count twice in a row**"
            )
            current_count = 0
            last_user_id = None
            return

        if value == current_count + 1:
            current_count += 1
            last_user_id = message.author.id
            await message.add_reaction("✅")
        else:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} **RUINED THE COUNT** at {current_count}. The next number is 1."
            )
            current_count = 0
            last_user_id = None


client.run(token)
