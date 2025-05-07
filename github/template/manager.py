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
from typing import Any, Dict

from jinja2 import Environment as JinjaEnvironment, Template

from mautrix.util import markdown

from ..config import Config
from .loader import ConfigTemplateLoader
from .proxy import TemplateProxy


class TemplateManager:
    _env: JinjaEnvironment
    _loader: ConfigTemplateLoader

    def __init__(self, config: Config, key: str) -> None:
        self._loader = ConfigTemplateLoader(config, key)
        self._env = JinjaEnvironment(
            loader=self._loader, lstrip_blocks=True, trim_blocks=True, extensions=["jinja2.ext.do"]
        )
        self._env.filters["markdown"] = lambda message: markdown.render(message, allow_html=True)

    def __getitem__(self, item: str) -> Template:
        return self._env.get_template(item)

    def reload(self) -> None:
        self._loader.reload()

    def proxy(self, args: Dict[str, Any]) -> TemplateProxy:
        return TemplateProxy(self._env, args)
