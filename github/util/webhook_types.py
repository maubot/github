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
from typing import Optional, NewType, List
from datetime import datetime

from mautrix.types import SerializableAttrs, SerializableEnum, serializer, deserializer, JSON

UnixDateTime = NewType("UnixDateTime", datetime)
ISODateTime = NewType("ISODateTime", datetime)
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@serializer(UnixDateTime)
def unix_datetime_serializer(dt: UnixDateTime) -> JSON:
    return int(dt.timestamp())


@deserializer(UnixDateTime)
def unix_datetime_deserializer(data: JSON) -> UnixDateTime:
    return UnixDateTime(datetime.utcfromtimestamp(data))


@serializer(ISODateTime)
def iso_datetime_serializer(dt: UnixDateTime) -> JSON:
    return dt.strftime(ISO_FORMAT)


@deserializer(ISODateTime)
def iso_datetime_deserializer(data: JSON) -> ISODateTime:
    return ISODateTime(datetime.strptime(data, ISO_FORMAT))


class User(SerializableAttrs['User']):
    name: str
    email: str
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


class GitUser(SerializableAttrs['GitUser']):
    name: str
    email: str
    username: Optional[str] = None


class License(SerializableAttrs['License']):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str


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

    created_at: UnixDateTime
    updated_at: Optional[ISODateTime]
    pushed_at: UnixDateTime

    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str

    homepage: Optional[str]
    size: int
    stargazers_count: int
    stargazers: int
    watchers_count: int
    watchers: int
    open_issues_count: int
    open_issues: int
    forks_count: int
    forks: int
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
    master_branch: int


class Commit(SerializableAttrs['Commit']):
    id: str
    tree_id: str
    distinct: bool
    message: str
    timestamp: ISODateTime
    url: str
    author: GitUser
    committer: GitUser
    added: List[str]
    removed: List[str]
    modified: List[str]


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
    created_at: ISODateTime
    updated_at: Optional[ISODateTime]
    uploader: User


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

    created_at: ISODateTime
    published_at: ISODateTime

    url: str
    assets_url: str
    upload_url: str
    tarball_url: str
    zipball_url: str
    html_url: str

    asset: List[ReleaseAsset]


class ReleaseAction(SerializableEnum):
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    PRERELEASED = "prereleased"


class ReleaseEvent(SerializableAttrs['ReleaseEvent']):
    action: ReleaseAction
    release: Release
    repository: Repository
    sender: User


class StarAction(SerializableEnum):
    CREATED = "created"
    DELETED = "deleted"


class StarEvent(SerializableAttrs['StarEvent']):
    action: StarAction
    starred_at: ISODateTime
    repository: Repository
    sender: User


class WatchAction(SerializableEnum):
    STARTED = "started"


class WatchEvent(SerializableAttrs['StarEvent']):
    action: WatchAction
    repository: Repository
    sender: User


class ForkEvent(SerializableAttrs['ForkEvent']):
    forkee: Repository
    repository: Repository


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
    created_at: ISODateTime
    updated_at: Optional[ISODateTime]
    due_on: Optional[ISODateTime]
    closed_at: Optional[ISODateTime]

    url: str
    html_url: str
    labels_url: str


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

    assignee: Optional[User]
    assignees: List[User]

    comments: int
    created_at: ISODateTime
    updated_at: Optional[ISODateTime]
    closed_at: Optional[ISODateTime]

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


class IssuesEvent(SerializableAttrs['IssuesEvent']):
    action: IssueAction
    issue: Issue
    changes: JSON
    repository: Repository
    sender: User

# TODO: Label, IssueComment, CommitComment, PullRequest, PullRequestReview, PullRequestReviewComment
#       RepositoryEvent, etc
