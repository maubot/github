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
from typing import Optional, NewType, List, Union
from datetime import datetime

from attr import dataclass
import attr

from mautrix.types import SerializableAttrs, SerializableEnum, serializer, deserializer, JSON

HubDateTime = NewType("HubDateTime", datetime)
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@serializer(HubDateTime)
def datetime_serializer(dt: HubDateTime) -> JSON:
    return dt.strftime(ISO_FORMAT)


@deserializer(HubDateTime)
def datetime_deserializer(data: JSON) -> HubDateTime:
    if isinstance(data, int):
        return HubDateTime(datetime.utcfromtimestamp(data))
    else:
        return HubDateTime(datetime.strptime(data, ISO_FORMAT))


@dataclass
class User(SerializableAttrs['User']):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    type: str
    site_admin: bool

    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str

    name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class GitUser(SerializableAttrs['GitUser']):
    name: str
    email: str
    username: Optional[str] = None


@dataclass
class License(SerializableAttrs['License']):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str


@dataclass
class Repository(SerializableAttrs['Repository']):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: User
    html_url: str
    description: Optional[str]
    fork: bool
    url: str

    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str

    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    pushed_at: Optional[HubDateTime]

    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str

    homepage: Optional[str]
    size: int
    stargazers_count: int
    watchers_count: int
    open_issues_count: int
    forks_count: int
    language: str
    license: Optional[License]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    mirror_url: Optional[str]
    archived: bool
    disabled: bool
    default_branch: str


@dataclass
class Commit(SerializableAttrs['Commit']):
    id: str
    tree_id: str
    distinct: bool
    message: str
    timestamp: HubDateTime
    url: str
    author: GitUser
    committer: GitUser
    added: List[str]
    removed: List[str]
    modified: List[str]


@dataclass
class PushEvent(SerializableAttrs['PushEvent']):
    ref: str
    before: str
    after: str
    created: bool
    deleted: bool
    forced: bool
    base_ref: Optional[str]
    compare: str
    commits: List[Commit]
    head_commit: Optional[Commit]

    repository: Repository
    pusher: GitUser
    sender: User


@dataclass
class ReleaseAsset(SerializableAttrs['ReleaseAsset']):
    id: int
    node_id: int
    url: str
    browser_download_url: str
    name: str
    label: str
    state: str
    content_type: str
    size: int
    download_count: str
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    uploader: User


@dataclass
class Release(SerializableAttrs['Release']):
    id: int
    node_id: str
    tag_name: str
    target_commitish: str
    name: Optional[str]
    draft: bool
    prerelease: bool
    author: User
    body: Optional[str]

    created_at: HubDateTime
    published_at: Optional[HubDateTime]

    url: str
    assets_url: str
    upload_url: str
    tarball_url: str
    zipball_url: str
    html_url: str

    assets: List[ReleaseAsset]


class ReleaseAction(SerializableEnum):
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    PRERELEASED = "prereleased"


@dataclass
class ReleaseEvent(SerializableAttrs['ReleaseEvent']):
    action: ReleaseAction
    release: Release
    repository: Repository
    sender: User


class StarAction(SerializableEnum):
    CREATED = "created"
    DELETED = "deleted"


@dataclass
class StarEvent(SerializableAttrs['StarEvent']):
    action: StarAction
    starred_at: HubDateTime
    repository: Repository
    sender: User


class WatchAction(SerializableEnum):
    STARTED = "started"


@dataclass
class WatchEvent(SerializableAttrs['StarEvent']):
    action: WatchAction
    repository: Repository
    sender: User


@dataclass
class ForkEvent(SerializableAttrs['ForkEvent']):
    forkee: Repository
    repository: Repository
    sender: User


@dataclass
class Label(SerializableAttrs['Label']):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool


class IssueState(SerializableEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Milestone(SerializableAttrs['Milestone']):
    id: int
    node_id: str
    number: int
    title: str
    description: str

    creator: User
    open_issues: int
    closed_issues: int
    state: IssueState
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    due_on: Optional[HubDateTime]
    closed_at: Optional[HubDateTime]

    url: str
    html_url: str
    labels_url: str


@dataclass
class Issue(SerializableAttrs['Issue']):
    id: int
    node_id: str
    number: int
    title: str
    body: str

    user: User
    author_association: str
    labels: List[Label]
    state: IssueState
    locked: bool
    milestone: Optional[Milestone]

    assignees: List[User]

    comments: int
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    closed_at: Optional[HubDateTime]

    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    events_url: str
    html_url: str


class IssueAction(SerializableEnum):
    OPENED = "opened"
    EDITED = "edited"
    DELETED = "deleted"
    PINNED = "pinned"
    UNPINNED = "unpinned"
    CLOSED = "closed"
    REOPENED = "reopened"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    TRANSFERRED = "transferred"
    MILESTONED = "milestoned"
    DEMILESTONED = "demilestoned"


@dataclass
class Change(SerializableAttrs['Change']):
    original: str = attr.ib(metadata={"json": "from"})


@dataclass
class IssueChanges(SerializableAttrs['IssueChanges']):
    body: Change
    title: Change


@dataclass
class IssuesEvent(SerializableAttrs['IssuesEvent']):
    action: IssueAction
    issue: Issue
    repository: Repository
    sender: User
    assignee: Optional[User] = None
    label: Optional[Label] = None
    milestone: Optional[Milestone] = None
    changes: Optional[JSON] = None


@dataclass
class Comment(SerializableAttrs['Comment']):
    id: int
    node_id: int
    url: str
    html_url: str
    body: str
    user: User
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]


class IssueCommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class IssueCommentEvent(SerializableAttrs['IssueCommentEvent']):
    action: IssueCommentAction
    issue: Issue
    comment: Comment
    repository: Repository
    sender: User


@dataclass
class WebhookResponse(SerializableAttrs['WebhookResponse']):
    code: Optional[int]
    status: str
    message: Optional[str]


@dataclass
class WebhookConfig(SerializableAttrs['WebhookConfig']):
    url: str
    content_type: Optional[str] = None
    secret: Optional[str] = None
    insecure_ssl: Optional[str] = None


@dataclass
class Webhook(SerializableAttrs['Webhook']):
    id: int
    type: str
    name: str
    active: bool
    events: List[str]
    config: WebhookConfig
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    url: str
    test_url: str
    ping_url: str
    last_response: WebhookResponse


@dataclass
class PingEvent(SerializableAttrs['PingEvent']):
    zen: str
    hook_id: int
    hook: Webhook


@dataclass
class CreateEvent(SerializableAttrs['CreateEvent']):
    ref_type: str
    ref: str
    master_branch: str
    description: Optional[str]
    pusher_type: str
    repository: Repository
    sender: User


# TODO: Label, CommitComment, PullRequest, PullRequestReview, PullRequestReviewComment
#       RepositoryEvent, etc


Event = Union[IssuesEvent, IssueCommentEvent, PushEvent, ReleaseEvent, StarEvent, WatchEvent,
              PingEvent]

EVENT_TYPES = {
    "issues": IssuesEvent,
    "issue_comment": IssueCommentEvent,
    "push": PushEvent,
    "release": ReleaseEvent,
    "star": StarEvent,
    "watch": WatchEvent,
    "ping": PingEvent,
    "fork": ForkEvent,
    "create": CreateEvent,
}

ACTION_TYPES = {
    "IssueAction": IssueAction,
    "StarAction": StarAction,
    "IssueCommentAction": IssueCommentAction,
    "ReleaseAction": ReleaseAction,
}
