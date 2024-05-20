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
import sys
import threading
from dataclasses import dataclass, field
from typing import Optional

import discord
from dotenv import load_dotenv

COUNT_PATH = pathlib.Path().absolute() / "data" / "count.json"

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@dataclass
class Count:
    """
    A class that represents the count and the last user ID who incremented the count.

    Attributes:
        count (int): The current count.
        last_user_id (Optional[int]): The ID of the last user who incremented the count.
        ignore_repeated_users (bool): Whether to ignore when the same user increments the count twice in a row.
        highest_count (int): The highest count reached.
        highest_count_user (Optional[int]): The ID of the user who reached the highest count.
        _mutex (threading.Lock): A mutex to ensure thread safety.
    """

    count: int = 0
    last_user_id: Optional[int] = None
    ignore_repeated_users: bool = False
    highest_count: int = 0
    highest_count_user: Optional[int] = None
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
                "highest_count": self.highest_count,
                "highest_count_user": self.highest_count_user,
            }

    @classmethod
    def from_dict(cls, data: dict) -> "Count":
        """
        Creates a Count object from a dictionary.
        :param data: The dictionary containing the data.
        :return: The Count object.
        """

        highest_count = data.get("highest_count") or 0
        highest_count_user = data.get("highest_count_user") or None

        return cls(
            data["count"],
            data["last_user_id"],
            data["ignore_repeated_users"],
            highest_count,
            highest_count_user,
        )

    def reset(self):
        """
        Resets the count to 0 and clears the last user ID.
        """

        with self._mutex:
            self.count = 0
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

            if self.count > self.highest_count:
                self.highest_count = self.count
                self.highest_count_user = user_id
                return True
            return False


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
    is_bot_message = message.author == client.user
    is_counting_channel = message.channel.id == counting_channel
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
            if current_count.increment_to(value, message.author.id):
                print(
                    f"New highest count: {current_count.highest_count} by {message.author.id} at "
                    f"{current_count.current_count}, next number is {current_count.next_count}"
                )

                await message.add_reaction("🎉")
                await message.channel.send(
                    f"{message.author.mention} **BEAT THE HIGHEST COUNT** at {current_count.current_count}! "
                    f"The highest count is now {current_count.highest_count} by <@{current_count.highest_count_user}>."
                )
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


client.run(token)
