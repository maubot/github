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
from typing import Any, Callable, Iterable, Tuple

from jinja2 import BaseLoader, TemplateNotFound

from ..config import Config
from ..util import recursive_get


class ConfigTemplateLoader(BaseLoader):
    config: Config
    field: str
    reload_counter: int

    def __init__(self, config: Config, field: str) -> None:
        self.config = config
        self.field = field
        self.reload_counter = 0

    def reload(self) -> None:
        self.reload_counter += 1

    def get_source(self, environment: Any, name: str) -> Tuple[str, str, Callable[[], bool]]:
        cur_reload_counter = self.reload_counter
        try:
            tpl = recursive_get(self.config[self.field], name)
        except KeyError:
            raise TemplateNotFound(name)
        if not tpl:
            raise TemplateNotFound(name)
        return (
            self.config["macros"] + tpl,
            name,
            lambda: self.reload_counter == cur_reload_counter,
        )

    def list_templates(self) -> Iterable[str]:
        return sorted(self.config[self.field].keys())
