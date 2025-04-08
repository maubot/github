# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import List, Callable

from ..util import contrast, hex_to_rgb


class TemplateUtil:
    contrast_threshold = 4.5
    white_rgb = (1, 1, 1)
    white_hex = "ffffff"
    black_hex = "000000"

    @classmethod
    def contrast_fg(cls, color: str) -> str:
        return (cls.white_hex
                if contrast(hex_to_rgb(color), cls.white_rgb) >= cls.contrast_threshold
                else cls.black_hex)

    @staticmethod
    def cut_message(message: str, max_len: int = 72) -> str:
        if "\n" in message:
            message = message.split("\n")[0]
            if len(message) <= max_len:
                message += " […]"
                return message
        if len(message) > max_len:
            message = message[:max_len] + "…"
        return message

    @staticmethod
    def ref_type(ref: str) -> str:
        if ref.startswith("refs/heads/"):
            return "branch"
        elif ref.startswith("refs/tags/"):
            return "tag"
        else:
            return "ref"

    @staticmethod
    def ref_name(ref: str) -> str:
        return ref.split("/", 2)[2]

    @staticmethod
    def ref_is_personal(ref: str) -> bool:
        # Detect personal branches
        # return True if branch name contains '/', like in
        #     "refs/heads/username/some-branch"
        return '/' in ref.split("/", 2)[2]

    @staticmethod
    def join_human_list(data: List[str], *, joiner: str = ", ", final_joiner: str = " and ",
                        mutate: Callable[[str], str] = lambda val: val) -> str:
        if not data:
            return ""
        elif len(data) == 1:
            return mutate(data[0])
        return joiner.join(mutate(val) for val in data[:-1]) + final_joiner + mutate(data[-1])
