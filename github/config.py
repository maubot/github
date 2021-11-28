# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2021 Tulir Asokan
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
import string
import random

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

secret_charset = string.ascii_letters + string.digits


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("client_id")
        helper.copy("client_secret")
        helper.base["webhook_key"] = ("".join(random.choices(secret_charset, k=64))
                                      if helper.source.get("webhook_key", "generate") == "generate"
                                      else helper.source["webhook_key"])
        helper.copy("global_webhook_secret")
        helper.copy("reset_tokens")
        helper.copy("command_options.prefix")
        helper.copy("message_options.msgtype")
        helper.copy("message_options.aggregation_timeout")
        helper.copy("templates")
        helper.copy("macros")
        helper.copy_dict("messages")
