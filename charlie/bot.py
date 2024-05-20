"""
This module contains the code for the Discord bot that will be used to count in the Discord channel.
"""

#  This file is part of charlie.
#
#  charlie is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  charlie is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with charlie. If not,
#  see <https://www.gnu.org/licenses/>.

import json
import os
import pathlib
import signal
import sys
import threading
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from .leaderboard import Leaderboard

COUNT_PATH = pathlib.Path().absolute() / "data" / "count.json"

load_dotenv()


@dataclass
class Count:
    """
    A class that represents the count and the last user ID who incremented the count.

    :cvar count: The current count.
    :cvar last_user_id: The ID of the last user who incremented the count.
    :cvar ignore_repeated_users: Whether to ignore when the same user increments the count twice in a row.
    :cvar leaderboard: The leaderboard.
    """

    count: int = 0
    last_user_id: Optional[int] = None
    ignore_repeated_users: bool = False
    leaderboard: Leaderboard = field(default_factory=Leaderboard)
    _mutex: threading.Lock = field(default_factory=threading.Lock)

    def to_dict(self) -> dict:
        """
        Converts the Count object to a dictionary.
        :return: The dictionary containing the data.
        """

        with self._mutex:
            return {
                "count": self.count,
                "last_user_id": self.last_user_id,
                "ignore_repeated_users": self.ignore_repeated_users,
                "leaderboard": self.leaderboard.to_dict(),
            }

    @classmethod
    def from_dict(cls, data: dict) -> "Count":
        """
        Creates a Count object from a dictionary.
        :param data: The dictionary containing the data.
        :return: The Count object.
        """

        highest_count = data.get("highest_count")
        highest_count_user = data.get("highest_count_user")

        leaderboard = data.get("leaderboard")
        if leaderboard is not None:
            leaderboard = Leaderboard.from_dict(leaderboard)
        else:
            leaderboard = Leaderboard()

        if highest_count is not None and highest_count_user is not None:
            leaderboard.record_entry(highest_count_user, highest_count)

        return cls(
            data["count"],
            data["last_user_id"],
            data["ignore_repeated_users"],
            leaderboard,
        )

    def reset(self, count: int = 0):
        """
        Resets the count to the given count and clears the last user ID.
        :param count: The count to reset to.
        """

        with self._mutex:
            self.count = count
            self.last_user_id = None

    def save(self, path):
        """
        Saves the count to a file.
        :param path: The path to the file.
        """

        with open(path, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path) -> "Count":
        """
        Loads the count from a file.
        :param path: The path to the file.
        :return: The loaded count.
        """

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @property
    def current_count(self) -> int:
        """
        Returns the current count.
        :return: The current count.
        """

        return 1 if self.count == 0 else self.count

    @property
    def next_count(self) -> int:
        """
        Returns the next count.
        :return: The next count.
        """

        return self.count + 1

    @property
    def count_after_reset(self) -> int:
        """
        Returns the count after the reset.
        """

        return 1

    def can_user_increment(self, user_id: int) -> bool:
        """
        Checks if the count can be incremented by the user.
        :param user_id: The ID of the user who wants to increment the count.
        :return: True if the count can be incremented, False otherwise.
        """

        if self.ignore_repeated_users:
            return True

        with self._mutex:
            return self.last_user_id != user_id

    def can_increment_to(self, value: int) -> bool:
        """
        Checks if the count can be incremented to the given value.
        :param value: The value to increment to.
        :return: True if the count can be incremented, False otherwise.
        """

        with self._mutex:
            return value == self.next_count

    def increment_to(self, value: int, user_id: int) -> bool:
        """
        Increments the count to the given value by the user and checks if the count has beaten the highest count.
        :param value: The value to increment to.
        :param user_id: The ID of the user who incremented the count.
        :return: True if the count has beaten the highest count, False otherwise.
        """
        assert self.can_user_increment(user_id), "User cannot increment the count."
        assert self.can_increment_to(
            value
        ), "Count cannot be incremented to the given value."

        with self._mutex:
            self.count += 1
            self.last_user_id = user_id
            return self.leaderboard.record_entry(user_id, value)


# Load environment variables
if (channel_id := os.getenv("CHANNEL_ID")) is not None:
    try:
        counting_channel = int(channel_id)
    except ValueError:
        print("Environment variable CHANNEL_ID must be an integer.", file=sys.stderr)
        sys.exit(1)
else:
    print("Missing environment variable CHANNEL_ID.", file=sys.stderr)
    sys.exit(1)

token = os.getenv("TOKEN")

if token is None:
    print("Missing environment variable TOKEN.", file=sys.stderr)
    sys.exit(1)

if (testing_guild := os.getenv("TESTING_GUILD")) is not None:
    try:
        testing_guild_id = discord.Object(int(testing_guild))
    except ValueError:
        print("Environment variable TESTING_GUILD must be an integer.", file=sys.stderr)
        sys.exit(1)
else:
    testing_guild_id = None

# Create the data directory if it doesn't exist and load the count from the file.
os.makedirs(COUNT_PATH.parent, exist_ok=True)

try:
    current_count = Count.load(COUNT_PATH)
    print(
        f"Loaded count from file {COUNT_PATH}, current count is {current_count.current_count}, next count is "
        f"{current_count.next_count}."
    )
    current_count.save(COUNT_PATH)
except FileNotFoundError:
    current_count = Count()
    current_count.save(COUNT_PATH)
    print(f"Count file {COUNT_PATH} not found, created a new count file.")
except json.JSONDecodeError as e:
    print(f"Failed to load count from file {COUNT_PATH}: {e}", file=sys.stderr)
    sys.exit(1)
except KeyError as e:
    print(
        f"Failed to load count from file {COUNT_PATH}: Missing key {e}", file=sys.stderr
    )
    sys.exit(1)
except ValueError as e:
    print(f"Failed to load count from file {COUNT_PATH}: {e}", file=sys.stderr)
    sys.exit(1)


def parse_message(message: str) -> Optional[int]:
    """
    Parses a message and returns the number in the message if any.
    :param message: The message to parse.
    :return: The number in the message if any, None otherwise.
    """
    if len(message) == 0:
        return None

    i = 0
    number = ""
    while i < len(message) and message[i].isdigit():
        number += message[i]
        i += 1

    if len(number) == 0:
        return None

    return int(number)


intents = discord.Intents.default()
intents.message_content = True


class Client(discord.Client):
    """
    A subclass of discord.Client that includes a command tree.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # Copy the global commands to the testing guild if it exists or sync all commands globally.
        if testing_guild_id is not None:
            self.tree.copy_global_to(guild=testing_guild_id)
            await self.tree.sync(guild=testing_guild_id)
        else:
            await self.tree.sync()


client = Client(intents=intents)


# Handle SIGINT and SIGTERM signals to save the count before exiting.
def signal_handler(_sig, _frame):
    current_count.save(COUNT_PATH)
    client.loop.create_task(client.close())
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
    global current_count

    # Ignore messages from the bot and messages from channels that are not the counting channel.
    is_self_message = message.author == client.user
    is_counting_channel = message.channel.id == counting_channel
    is_bot_message = message.author.bot or is_self_message
    if is_bot_message or not is_counting_channel:
        return

    # Check if the message is a number.
    if (value := parse_message(message.content)) is not None:
        if not current_count.can_user_increment(message.author.id):
            print(
                f"Failed to increment count to {value} by {message.author.id}, current count was "
                f"{current_count.current_count}, next number is {current_count.count_after_reset}"
            )

            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} **RUINED THE COUNT** at {current_count.current_count}. The next number is "
                f"{current_count.count_after_reset}. **You can't count twice in a row**"
            )
            current_count.reset()
            current_count.save(COUNT_PATH)
            return

        if current_count.can_increment_to(value):
            highest_count = (
                current_count.leaderboard.highest_count(message.author.id) or 0
            )
            current_rank = current_count.leaderboard.rank(message.author.id)

            if current_count.increment_to(value, message.author.id):
                new_highest_count = current_count.leaderboard.highest_count(
                    message.author.id
                )
                new_rank = current_count.leaderboard.rank(message.author.id)

                print(
                    f"User {message.author.id} has beaten their highest count, new highest count is "
                    f"{new_highest_count}, last highest count was {highest_count}"
                )

                await message.add_reaction("🎉")

                content = (
                    f"{message.author.mention} **BEAT THEIR HIGHEST COUNT** at {new_highest_count}. Last personal "
                    f"record was {highest_count}."
                )

                if current_rank is not None and new_rank < current_rank:
                    print(
                        f"User {message.author.id} has beaten their rank, new rank is {new_rank}, last rank was "
                        f"{current_rank}."
                    )

                    previous_ranked_entry = current_count.leaderboard.get_entry_by_rank(
                        new_rank + 1
                    )
                    if previous_ranked_entry is not None:
                        previous_ranked_user = await message.guild.fetch_member(
                            previous_ranked_entry.user_id
                        )

                        await message.add_reaction("🌟")
                        content += (
                            f"\nAnd, also **BEAT THEIR RANK** at #{new_rank}. Last rank was #{current_rank}, "
                            f"beating {previous_ranked_user.mention}."
                        )
                    else:
                        await message.add_reaction("⭐")
                        content += f"\nAnd, also **BEAT THEIR RANK** at #{new_rank}. Last rank was #{current_rank}."

                await message.channel.send(content)
            else:
                print(
                    f"Count incremented to {current_count.current_count} by {message.author.id}, "
                    f"next number is {current_count.next_count}"
                )

                await message.add_reaction("✅")
        else:
            print(
                f"Failed to increment count to {value} by {message.author.id}, current count was "
                f"{current_count.current_count}, next number is {current_count.count_after_reset}"
            )

            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} **RUINED THE COUNT** at {current_count.current_count}. The next number is "
                f"{current_count.count_after_reset}."
            )
            current_count.reset()

        current_count.save(COUNT_PATH)


@client.tree.command()
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
async def reset_count(interaction: discord.Interaction, count: Optional[int] = None):
    """
    Resets the count to the given count.
    """
    global current_count

    if interaction.channel.id != counting_channel:
        return

    count = count or 0

    current_count.reset(count)
    current_count.save(COUNT_PATH)

    await interaction.response.send_message(f"The count has been reset to {count}.")


@client.tree.command()
@app_commands.guild_only()
async def leaderboard(interaction: discord.Interaction):
    """
    Shows the leaderboard.
    """
    global current_count

    if interaction.channel.id != counting_channel:
        return

    await interaction.response.defer()

    entries = current_count.leaderboard.top_entries(10)

    embed = discord.Embed(title="Leaderboard", color=discord.Color.blurple())
    embed.set_footer(text="You are not ranked yet.")

    personal_entry = current_count.leaderboard.get_entry(interaction.user.id)
    if personal_entry is not None:
        embed.set_footer(
            text=(
                f"{interaction.user.name}, your rank is #{personal_entry.rank}, your highest count is "
                f"{personal_entry.highest_count}."
            )
        )

    description = ""
    for entry in entries:
        user = await interaction.guild.fetch_member(entry.user_id)

        description += f"`#{entry.rank}` ・ {user.mention} ・ Highest count: **{entry.highest_count}**\n"

    if not description:
        description = "No entries yet."

    embed.description = description

    await interaction.followup.send(embed=embed)


client.run(token)
