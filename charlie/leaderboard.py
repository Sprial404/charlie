"""
This module contains classes for storing leaderboard data.
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

import bisect
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LeaderboardEntry:
    """
    This class is used to store leaderboard entry data.

    :cvar user_id: The user's ID.
    :cvar highest_count: The user's highest count.
    :cvar last_highest_count: The user's last highest count.
    :cvar times_counted: The number of times the user has counted.
    :cvar mistakes_made: The number of mistakes the user has made.
    """

    user_id: int
    highest_count: int
    last_highest_count: int = 0
    times_counted: int = 0
    mistakes_made: int = 0
    rank: int = 0
    last_rank: int = 0

    def to_dict(self) -> dict:
        """
        Converts the leaderboard entry to a dictionary.

        :return: The leaderboard entry as a dictionary.
        """

        return {
            "user_id": self.user_id,
            "highest_count": self.highest_count,
            "last_highest_count": self.last_highest_count,
            "times_counted": self.times_counted,
            "mistakes_made": self.mistakes_made,
            "rank": self.rank,
            "last_rank": self.last_rank,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LeaderboardEntry":
        """
        Creates a leaderboard entry from a dictionary.

        :param data: The dictionary to create the leaderboard entry from.
        :return: The created leaderboard entry.
        """

        return cls(
            data["user_id"],
            data["highest_count"],
            data["last_highest_count"],
            data["times_counted"],
            data["mistakes_made"],
            data["rank"],
            data["last_rank"],
        )


@dataclass
class Leaderboard:
    """
    This class is used to store leaderboard data.

    :cvar entries: The leaderboard entries sorted by highest count.
    :cvar user_ids: A mapping of user IDs to their index in the entries list.
    """

    entries: list[LeaderboardEntry] = field(default_factory=list)
    user_ids: dict[int, int] = field(default_factory=dict)

    def _reindex(self) -> None:
        """
        Reindex the user IDs.
        """

        for index, entry in enumerate(self.entries):
            self.user_ids[entry.user_id] = index
            self.entries[index].last_rank = self.entries[index].rank
            self.entries[index].rank = index + 1

    def record_entry(self, user_id: int, count: int) -> bool:
        """
        Adds a new entry to the leaderboard or updates an existing entry if the user already exists.

        :param user_id: The user's ID.
        :param count: The user's latest count.
        :return: True if their highest count was broken, False otherwise.
        """

        index = self.user_ids.get(user_id)

        # If the user doesn't exist, add them to the leaderboard.
        if index is None:
            entry = LeaderboardEntry(user_id, count, times_counted=1)
            bisect.insort_right(self.entries, entry, key=lambda x: -x.highest_count)
            self._reindex()
            return True

        # Else, update their entry.
        entry = self.entries[index]
        entry.times_counted += 1

        # If the user's highest count was broken, update it.
        if count > entry.highest_count:
            entry.last_highest_count = entry.highest_count
            entry.highest_count = count

            # If the user's new highest count is higher than the entry before them, move them up.
            if index > 0 and self.entries[index - 1].highest_count < count:
                new_index = bisect.bisect_right(
                    self.entries, -count, hi=index, key=lambda x: -x.highest_count
                )
                del self.entries[index]
                self.entries.insert(new_index, entry)
                self._reindex()
                return True

        return False

    def remove_entry(self, user_id: int) -> None:
        """
        Removes an entry from the leaderboard.

        :param user_id: The user's ID.
        """

        if user_id in self.user_ids:
            entry_index = self.user_ids[user_id]
            del self.entries[entry_index]
            self._reindex()

    def get_entry(self, user_id: int) -> Optional[LeaderboardEntry]:
        """
        Gets an entry from the leaderboard.

        :param user_id: The user's ID.
        :return: The leaderboard entry if it exists, None otherwise.
        """

        if user_id not in self.user_ids:
            return None

        return self.entries[self.user_ids[user_id]]

    def get_entry_by_rank(self, rank: int) -> Optional[LeaderboardEntry]:
        """
        Gets an entry from the leaderboard by rank.

        :param rank: The rank of the entry.
        :return: The leaderboard entry if it exists, None otherwise.
        """

        if 1 <= rank <= len(self.entries):
            return self.entries[rank - 1]

        return None

    def top_entries(self, n: int) -> list[LeaderboardEntry]:
        """
        Gets the top n entries from the leaderboard.

        :param n: The number of entries to get.
        :return: The top n entries.
        """

        return self.entries[:n]

    def highest_count(self, user_id: int) -> Optional[int]:
        """
        Gets the highest count of a user in the leaderboard.

        :param user_id: The user's ID.
        :return: The user's highest count if they exist in the leaderboard, None otherwise.
        """

        if user_id not in self.user_ids:
            return None

        return self.entries[self.user_ids[user_id]].highest_count

    def last_highest_count(self, user_id: int) -> Optional[int]:
        """
        Gets the last highest count of a user in the leaderboard.

        :param user_id: The user's ID.
        :return: The user's last highest count if they exist in the leaderboard, None otherwise.
        """

        if user_id not in self.user_ids:
            return None

        return self.entries[self.user_ids[user_id]].last_highest_count

    def rank(self, user_id: int) -> Optional[int]:
        """
        Gets the rank of a user in the leaderboard.

        :param user_id: The user's ID.
        :return: The user's rank if they exist in the leaderboard, None otherwise.
        """

        if user_id not in self.user_ids:
            return None

        return self.entries[self.user_ids[user_id]].rank

    def last_rank(self, user_id: int) -> Optional[int]:
        """
        Gets the last rank of a user in the leaderboard.

        :param user_id: The user's ID.
        :return: The user's last rank if they exist in the leaderboard, None otherwise.
        """

        if user_id not in self.user_ids:
            return None

        return self.entries[self.user_ids[user_id]].last_rank

    def to_dict(self) -> dict:
        """
        Converts the leaderboard to a dictionary.

        :return: The leaderboard as a dictionary.
        """

        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "user_ids": self.user_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Leaderboard":
        """
        Creates a leaderboard from a dictionary.

        :param data: The dictionary to create the leaderboard from.
        :return: The created leaderboard.
        """

        leaderboard = cls()
        leaderboard.entries = [
            LeaderboardEntry.from_dict(entry_data) for entry_data in data["entries"]
        ]
        leaderboard.user_ids = {
            int(user_id): index for user_id, index in data["user_ids"].items()
        }
        return leaderboard
