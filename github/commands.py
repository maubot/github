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
from typing import Tuple, Optional, TYPE_CHECKING
import json

from maubot import MessageEvent
from maubot.handlers import command

from .api import GitHubClient

if TYPE_CHECKING:
    from .bot import GitHubBot


def authenticated(_outer_fn=None, *, required: bool = True):
    def decorator(fn):
        async def wrapper(self: 'Commands', evt: MessageEvent, **kwargs):
            client = self.bot.clients.get(evt.sender)
            if required and (not client or not client.token):
                return await evt.reply("You're not logged in. Log in with `!github login` first.")
            return await fn(self, evt, **kwargs, client=client)

        return wrapper

    return decorator(_outer_fn) if _outer_fn else decorator


repo_syntax = r"([A-Za-z0-9-_]+)/([A-Za-z0-9-_]+)"


class Commands:
    bot: 'GitHubBot'

    def __init__(self, bot: 'GitHubBot') -> None:
        self.bot = bot

    @command.new("github", require_subcommand=True)
    async def github(self, evt: MessageEvent) -> None:
        pass

    @github.subcommand("login", help="Log into GitHub.")
    async def login(self, evt: MessageEvent) -> None:
        redirect_url = (self.bot.webapp_url / "auth").with_query({"user_id": evt.sender})
        login_url = str(self.bot.clients.get(evt.sender, create=True).get_login_url(
            redirect_uri=redirect_url,
            scope="user:user public_repo repo admin:repo_hook"))
        await evt.reply(f"[Click here to log in]({login_url})")

    @github.subcommand("ping", help="Check your login status.")
    async def ping(self, evt: MessageEvent) -> None:
        client = self.bot.clients.get(evt.sender)
        if not client or not client.token:
            await evt.reply("You're not logged in. Log in with `!github login` first.")
            return
        username = await client.query("viewer { login }", path="viewer.login")
        await evt.reply(f"You're logged in as @{username}")

    @github.subcommand("raw", help="Make a raw GraphQL query.")
    @command.argument("query", required=True, pass_raw=True)
    @authenticated
    async def raw_query(self, evt: MessageEvent, query: str, client: GitHubClient) -> None:
        client = self.bot.clients.get(evt.sender)
        if not client or not client.token:
            await evt.reply("You're not logged in. Log in with `!github login` first.")
            return
        variables = {}
        if "---" in query:
            query, variables = query.split("---")
            try:
                variables = json.loads(variables)
            except json.JSONDecodeError as err:
                await evt.reply(f"Failed to parse variables: {err}")
                return
        resp = await client.call_raw(query, variables)
        await evt.reply("<pre><code class='language-json'>"
                        f"{json.dumps(resp, indent=2)}"
                        "</code></pre>", allow_html=True)

    @github.subcommand("create", help="Create an issue.")
    @command.argument("repo", required=False, matches=repo_syntax)
    @command.argument("data", required=True, pass_raw=True)
    @authenticated
    async def create_issue(self, evt: MessageEvent, repo: Tuple[str, str], data: str,
                           client: GitHubClient) -> None:
        title, body = data.split("\n", 1) if "\n" in data else (data, "")
        repo_id = await client.query(query="repository (name: $name, owner: $owner) { id }",
                                     args="$owner: String!, $name: String!",
                                     variables={"owner": repo[0], "name": repo[1]},
                                     path="repository.id")
        issue = await client.mutate(query="createIssue(input: $input) { issue { number url } }",
                                    args="$input: CreateIssueInput!",
                                    variables={"input": {
                                        "repositoryId": repo_id,
                                        "title": title,
                                        "body": body,
                                    }},
                                    path="createIssue.issue")
        await evt.reply(f"Created [issue #{issue['number']}]({issue['url']})")

    @github.subcommand("webhook", help="Manage webhooks.", required_subcommand=True)
    async def webhook(self, evt: MessageEvent, repo: Tuple[str, str], client: GitHubClient) -> None:
        pass

    @webhook.subcommand("list", help="List webhooks in this room.")
    async def webhook_list(self, evt: MessageEvent) -> None:
        hooks = self.bot.webhook_secrets.get_all_for_room(evt.room_id)
        info = "\n".join(f"* `{hook.repo}` added by "
                         f"[{hook.user_id}](https://matrix.to/#/{hook.user_id})"
                         for hook in hooks)
        await evt.reply(f"GitHub webhooks in this room:\n\n{info}")

    @webhook.subcommand("add", help="Add a webhook for this room.")
    @command.argument("repo", required=True, matches=repo_syntax)
    @authenticated
    async def webhook_create(self, evt: MessageEvent, repo: Tuple[str, str], client: GitHubClient
                             ) -> None:
        repo_name = f"{repo[0]}/{repo[1]}"
        existing = self.bot.webhook_secrets.find(repo_name, evt.room_id)
        if existing:
            await evt.reply("This room already has a webhook for that repo")
            # TODO webhook may be deleted on github side
            return
        webhook_info = self.bot.webhook_secrets.create(repo_name, evt.sender, evt.room_id)
        await client.create_webhook(*repo, self.bot.webapp_url / "webhook" / str(webhook_info.id),
                                    secret=webhook_info.secret, content_type="json",
                                    events=["*"])
        await evt.reply(f"Successfully created webhook for {repo_name}")

    @webhook.subcommand("remove", aliases=["delete", "rm", "del"])
    @command.argument("repo", required=True, matches=repo_syntax)
    @authenticated(required=False)
    async def webhook_remove(self, evt: MessageEvent, repo: Tuple[str, str],
                             client: Optional[GitHubClient]) -> None:
        repo_name = f"{repo[0]}/{repo[1]}"
        webhook_info = self.bot.webhook_secrets.find(repo_name, evt.room_id)
        if not webhook_info:
            await evt.reply("This room does not have a webhook for that repo")
            return
        self.bot.webhook_secrets.delete(webhook_info.id)
        if webhook_info.github_id:
            if client:
                await client.delete_webhook(*repo, hook_id=webhook_info.github_id)
                await evt.reply("Webhook deleted from GitHub")
            else:
                await evt.reply("Webhook deleted locally, but it may still exist on GitHub")
        else:
            await evt.reply("Webhook deleted")
