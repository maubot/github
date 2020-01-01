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
from typing import Dict, Any

from jinja2 import Environment as JinjaEnvironment, TemplateNotFound


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
