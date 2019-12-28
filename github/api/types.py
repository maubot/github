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
class IssuePullURLs(SerializableAttrs['IssuePullURLs']):
    diff_url: str
    html_url: str
    patch_url: str
    url: str


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

    pull_request: Optional[IssuePullURLs] = None


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
    body: Optional[Change] = None
    title: Optional[Change] = None


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
class IssueComment(SerializableAttrs['IssueComment']):
    id: int
    node_id: int
    url: str
    html_url: str
    body: str
    user: User
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]


class CommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class IssueCommentEvent(SerializableAttrs['IssueCommentEvent']):
    action: CommentAction
    issue: Issue
    comment: IssueComment
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
    url: Optional[str] = None
    test_url: Optional[str] = None
    ping_url: Optional[str] = None
    last_response: Optional[WebhookResponse] = None


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


class MetaAction(SerializableEnum):
    DELETED = 'deleted'


@dataclass
class MetaEvent(SerializableAttrs['MetaEvent']):
    action: MetaAction
    hook: Webhook
    hook_id: int
    repository: Repository
    sender: User


@dataclass
class CommitComment(SerializableAttrs['CommitComment']):
    id: int
    node_id: str
    user: User
    url: str
    html_url: str

    body: str
    author_association: str
    commit_id: str
    position: Optional[int]
    line: Optional[int]
    path: Optional[str]

    created_at: HubDateTime
    updated_at: Optional[HubDateTime]


@dataclass
class CommitCommentEvent(SerializableAttrs['CommitCommentEvent']):
    action: CommentAction
    comment: IssueComment
    repository: Repository
    sender: User


@dataclass
class MilestoneChanges(SerializableAttrs['MilestoneChanges']):
    title: Optional[Change] = None
    description: Optional[Change] = None
    due_on: Optional[Change] = None


class MilestoneAction(SerializableEnum):
    CREATED = "created"
    OPENED = "opened"
    EDITED = "edited"
    CLOSED = "closed"
    DELETED = "deleted"


@dataclass
class MilestoneEvent(SerializableAttrs['MilestoneEvent']):
    action: MilestoneAction
    milestone: Milestone
    repository: Repository
    sender: User
    changes: Optional[IssueChanges] = None


class LabelAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class LabelChanges(SerializableAttrs['LabelChanges']):
    name: Optional[Change] = None
    color: Optional[Change] = None


@dataclass
class LabelEvent(SerializableAttrs['LabelEvent']):
    action: LabelAction
    label: Label
    changes: LabelChanges
    repository: Repository
    sender: User


class WikiPageAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"


@dataclass
class WikiPageEvent(SerializableAttrs['WikiPageEvent']):
    action: WikiPageAction
    page_name: str
    title: str
    summary: Optional[str]
    sha: str
    html_url: str


@dataclass
class WikiEvent(SerializableAttrs['WikiEvent']):
    pages: List[WikiPageEvent]
    repository: Repository
    sender: User


@dataclass
class PublicEvent(SerializableAttrs['PublicEvent']):
    repository: Repository
    sender: User


class PullRequestState(SerializableEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class PullRequestRef(SerializableAttrs['PullRequestRef']):
    label: str
    ref: str
    sha: str
    user: User
    repo: Repository


class TeamPrivacy(SerializableEnum):
    SECRET = "secret"
    CLOSED = "closed"


class TeamPermission(SerializableEnum):
    PULL = "pull"
    PUSH = "push"
    ADMIN = "admin"


@dataclass
class Team(SerializableAttrs['Team']):
    id: int
    node_id: str
    name: str
    slug: str
    description: str
    privacy: TeamPrivacy
    permission: TeamPermission

    url: str
    html_url: str
    members_url: str
    repositories_url: str


@dataclass
class PartialPullRequest(SerializableAttrs['PartialPullRequest']):
    id: int
    node_id: str
    number: int
    state: PullRequestState
    locked: bool
    title: str
    body: str
    user: User

    labels: List[Label]
    milestone: Optional[Milestone]
    assignees: List[User]
    requested_reviewers: List[User]
    requested_teams: List[Team]

    author_association: str
    merge_commit_sha: str

    head: PullRequestRef
    base: PullRequestRef

    created_at: HubDateTime
    updated_at: Optional[HubDateTime]
    closed_at: Optional[HubDateTime]
    merged_at: Optional[HubDateTime]

    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    commits_url: str
    review_comments_url: str
    review_comment_url: str
    comments_url: str
    statuses_url: str


@dataclass
class PullRequest(PartialPullRequest, SerializableAttrs['PullRequest']):
    merged_by: Optional[User]

    draft: bool
    merged: bool
    mergeable: bool
    rebaseable: bool
    mergeable_state: str

    comments: int
    review_comments: int
    maintainer_can_modify: bool
    commits: int
    additions: int
    deletions: int
    changed_files: int


class PullRequestAction(SerializableEnum):
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    OPENED = "opened"
    EDITED = "edited"
    CLOSED = "closed"
    REOPENED = "reopened"
    SYNCHRONIZE = "synchronize"
    READY_FOR_REVIEW = "ready_for_review"
    LOCKED = "locked"
    UNLOCKED = "unlocked"


@dataclass
class PullRequestEvent(SerializableAttrs['PullRequestEvent']):
    action: PullRequestAction
    pull_request: PullRequest
    number: int
    repository: Repository
    sender: User
    changes: Optional[IssueChanges] = None
    label: Optional[Label] = None
    assignee: Optional[User] = None
    milestone: Optional[Milestone] = None
    requested_reviewer: Optional[User] = None


class PullRequestReviewAction(SerializableEnum):
    SUBMITTED = "submitted"
    EDITED = "edited"
    DISMISSED = "dismissed"


class ReviewState(SerializableEnum):
    COMMENTED = "commented"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Review(SerializableAttrs['Review']):
    id: int
    node_id: str
    user: User
    commit_id: str
    submitted_at: HubDateTime
    state: ReviewState
    html_url: str
    pull_request_url: str
    author_association: str
    body: Optional[str] = None


@dataclass
class ReviewChanges(SerializableAttrs['ReviewChanges']):
    body: Optional[Change] = None


@dataclass
class PullRequestReviewEvent(SerializableAttrs['PullRequestReviewEvent']):
    action: PullRequestReviewAction
    pull_request: PartialPullRequest
    review: Review
    repository: Repository
    sender: User
    changes: Optional[ReviewChanges] = None


class PullRequestReviewCommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class ReviewComment(SerializableAttrs['ReviewComment']):
    id: int
    node_id: str
    pull_request_review_id: int
    user: User
    url: str
    html_url: str

    body: str
    author_association: str
    commit_id: str
    original_commit_id: str
    diff_hunk: str
    position: int
    original_position: int
    path: str

    created_at: HubDateTime
    updated_at: Optional[HubDateTime]


@dataclass
class PullRequestReviewCommentEvent(SerializableAttrs['PullRequestReviewCommentEvent']):
    action: PullRequestReviewCommentAction
    pull_request: PartialPullRequest
    comment: ReviewComment
    repository: Repository
    sender: User
    changes: Optional[ReviewChanges] = None


Event = Union[IssuesEvent, IssueCommentEvent, PushEvent, ReleaseEvent, StarEvent, WatchEvent,
              PingEvent, ForkEvent, CreateEvent, MetaEvent, CommitCommentEvent, MilestoneEvent,
              LabelEvent, WikiEvent, PublicEvent, PullRequestEvent, PullRequestReviewEvent,
              PullRequestReviewCommentEvent]

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
    "meta": MetaEvent,
    "commit_comment": CommitCommentEvent,
    "milestone": MilestoneEvent,
    "label": LabelEvent,
    "gollum": WikiEvent,
    "public": PublicEvent,
    "pull_request": PullRequestEvent,
    "pull_request_review": PullRequestReviewEvent,
    "pull_request_review_comment": PullRequestReviewCommentEvent,
}

ACTION_TYPES = {
    "IssueAction": IssueAction,
    "StarAction": StarAction,
    "CommentAction": CommentAction,
    "ReleaseAction": ReleaseAction,
    "MetaAction": MetaAction,
    "MilestoneAction": MilestoneAction,
    "LabelAction": LabelAction,
    "WikiPageAction": WikiPageAction,
    "PullRequestAction": PullRequestAction,
    "PRAction": PullRequestAction,
    "PullRequestReviewAction": PullRequestReviewAction,
    "ReviewAction": PullRequestReviewAction,

    "ReviewState": ReviewState,
}
