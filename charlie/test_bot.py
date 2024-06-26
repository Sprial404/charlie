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


def add(a: int, b: int) -> int:
    return a + b


def test_it_works() -> None:
    assert add(1, 2) == 3
