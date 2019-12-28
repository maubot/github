# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2019 Tulir Asokan
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
from typing import Dict, List, Any

from jinja2 import Environment as JinjaEnvironment, Template, TemplateNotFound

from mautrix.util import markdown

from .config import Config, ConfigTemplateLoader
from .util import contrast, hex_to_rgb


class TemplateManager:
    _env: JinjaEnvironment
    _loader: ConfigTemplateLoader

    def __init__(self, config: Config, key: str) -> None:
        self._loader = ConfigTemplateLoader(config, key)
        self._env = JinjaEnvironment(loader=self._loader, lstrip_blocks=True, trim_blocks=True,
                                     extensions=["jinja2.ext.do"])
        self._env.filters["markdown"] = markdown.render

    def __getitem__(self, item: str) -> Template:
        return self._env.get_template(item)

    def reload(self) -> None:
        self._loader.reload()

    def proxy(self, args: Dict[str, Any]) -> 'TemplateProxy':
        return TemplateProxy(self._env, args)


class TemplateProxy:
    _env: JinjaEnvironment
    _args: Dict[str, Any]

    def __init__(self, env: JinjaEnvironment, args: Dict[str, Any]) -> None:
        self._env = env
        self._args = args

    def __getattr__(self, item: str) -> str:
        try:
            tpl = self._env.get_template(item)
        except TemplateNotFound:
            raise AttributeError(item)
        return tpl.render(**self._args)


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
    def cut_message(message: str, max_len: int = 50) -> str:
        if "\n" in message:
            message = message.split("\n")[0]
            if len(message) <= max_len:
                message += " […]"
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
    def join_human_list(data: List[str], joiner: str = ", ", final_joiner: str = " and ") -> str:
        if not data:
            return ""
        elif len(data) == 1:
            return data[0]
        return joiner.join(data[:-1]) + final_joiner + data[-1]
