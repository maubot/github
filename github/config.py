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
from typing import Tuple, Iterable, Any, Callable
import string
import random

from jinja2 import BaseLoader, TemplateNotFound

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from .util import recursive_get

secret_charset = string.ascii_letters + string.digits


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("client_id")
        helper.copy("client_secret")
        helper.base["webhook_key"] = ("".join(random.choices(secret_charset, k=64))
                                      if helper.source.get("webhook_key", "generate") == "generate"
                                      else helper.source["webhook_key"])
        helper.copy("msgtype")
        helper.copy("templates")
        helper.copy("macros")
        helper.copy_dict("messages")


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
        tpl = recursive_get(self.config[self.field], name)
        if not tpl:
            raise TemplateNotFound(name)
        return (self.config["macros"] + tpl, name,
                lambda: self.reload_counter == cur_reload_counter)

    def list_templates(self) -> Iterable[str]:
        return sorted(self.config[self.field].keys())
