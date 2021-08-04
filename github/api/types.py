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
from typing import Optional, NewType, List, Union, Type, Dict, Any
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
class User(SerializableAttrs):
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
class Organization(SerializableAttrs):
    id: int
    node_id: str
    login: str
    description: str

    url: str
    avatar_url: str
    repos_url: str
    public_members_url: str
    issues_url: str
    hooks_url: str
    events_url: str
    avatar_url: str


@dataclass
class GitUser(SerializableAttrs):
    name: str
    email: str
    username: Optional[str] = None


@dataclass
class License(SerializableAttrs):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str


@dataclass
class Repository(SerializableAttrs):
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

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "name": self.full_name,
        }


@dataclass
class Commit(SerializableAttrs):
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
class PushEvent(SerializableAttrs):
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

    size: int = None
    distinct_size: int = None


@dataclass
class ReleaseAsset(SerializableAttrs):
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
class Release(SerializableAttrs):
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
class ReleaseEvent(SerializableAttrs):
    action: ReleaseAction
    release: Release
    repository: Repository
    sender: User


class StarAction(SerializableEnum):
    CREATED = "created"
    DELETED = "deleted"


@dataclass
class StarEvent(SerializableAttrs):
    action: StarAction
    starred_at: HubDateTime
    repository: Repository
    sender: User


class WatchAction(SerializableEnum):
    STARTED = "started"


@dataclass
class WatchEvent(SerializableAttrs):
    action: WatchAction
    repository: Repository
    sender: User


@dataclass
class ForkEvent(SerializableAttrs):
    forkee: Repository
    repository: Repository
    sender: User


@dataclass
class Label(SerializableAttrs):
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
class Milestone(SerializableAttrs):
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
class IssuePullURLs(SerializableAttrs):
    diff_url: str
    html_url: str
    patch_url: str
    url: str


@dataclass
class Issue(SerializableAttrs):
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

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "number": self.number,
        }


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

    X_LABEL_AGGREGATE = "xyz.maubot.issue_label_aggregation"
    X_MILESTONE_CHANGED = "xyz.maubot.issue_milestone_changed"


@dataclass
class Change(SerializableAttrs):
    original: str = attr.ib(metadata={"json": "from"})


@dataclass
class IssueChanges(SerializableAttrs):
    body: Optional[Change] = None
    title: Optional[Change] = None


@dataclass
class IssuesEvent(SerializableAttrs):
    action: IssueAction
    issue: Issue
    repository: Repository
    sender: User
    assignee: Optional[User] = None
    label: Optional[Label] = None
    milestone: Optional[Milestone] = None
    changes: Optional[JSON] = None

    @property
    def issue_id(self) -> int:
        return self.issue.id

    def meta(self) -> Dict[str, Any]:
        return {
            "issue": self.issue.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class IssueComment(SerializableAttrs):
    id: int
    node_id: int
    url: str
    html_url: str
    body: str
    user: User
    created_at: HubDateTime
    updated_at: Optional[HubDateTime]

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id ,
            "node_id": self.node_id,
        }


class CommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class IssueCommentEvent(SerializableAttrs):
    action: CommentAction
    issue: Issue
    comment: IssueComment
    repository: Repository
    sender: User

    @property
    def issue_id(self) -> int:
        return self.issue.id

    def meta(self) -> Dict[str, Any]:
        return {
            "issue": self.issue.meta(),
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class WebhookResponse(SerializableAttrs):
    code: Optional[int]
    status: str
    message: Optional[str]


@dataclass
class WebhookConfig(SerializableAttrs):
    url: str
    content_type: Optional[str] = None
    secret: Optional[str] = None
    insecure_ssl: Optional[str] = None


@dataclass
class Webhook(SerializableAttrs):
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
class PingEvent(SerializableAttrs):
    zen: str
    hook_id: int
    hook: Webhook


@dataclass
class CreateEvent(SerializableAttrs):
    ref_type: str
    ref: str
    master_branch: str
    description: Optional[str]
    pusher_type: str
    repository: Repository
    sender: User


@dataclass
class DeleteEvent(SerializableAttrs):
    ref_type: str
    ref: str
    pusher_type: str
    repository: Repository
    sender: User


class MetaAction(SerializableEnum):
    DELETED = 'deleted'


@dataclass
class MetaEvent(SerializableAttrs):
    action: MetaAction
    hook: Webhook
    hook_id: int
    repository: Repository
    sender: User


@dataclass
class CommitComment(SerializableAttrs):
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

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id ,
            "node_id": self.node_id,
            "commit_id": self.commit_id,
        }


@dataclass
class CommitCommentEvent(SerializableAttrs):
    action: CommentAction
    comment: CommitComment
    repository: Repository
    sender: User

    def meta(self) -> Dict[str, Any]:
        return {
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class MilestoneChanges(SerializableAttrs):
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
class MilestoneEvent(SerializableAttrs):
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
class LabelChanges(SerializableAttrs):
    name: Optional[Change] = None
    color: Optional[Change] = None


@dataclass
class LabelEvent(SerializableAttrs):
    action: LabelAction
    label: Label
    changes: LabelChanges
    repository: Repository
    sender: User


class WikiPageAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"


@dataclass
class WikiPageEvent(SerializableAttrs):
    action: WikiPageAction
    page_name: str
    title: str
    summary: Optional[str]
    sha: str
    html_url: str


@dataclass
class WikiEvent(SerializableAttrs):
    pages: List[WikiPageEvent]
    repository: Repository
    sender: User


@dataclass
class PublicEvent(SerializableAttrs):
    repository: Repository
    sender: User


class PullRequestState(SerializableEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class PullRequestRef(SerializableAttrs):
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
class Team(SerializableAttrs):
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
class PartialPullRequest(SerializableAttrs):
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

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id ,
            "node_id": self.node_id,
            "number": self.number,
        }


@dataclass
class PullRequest(PartialPullRequest, SerializableAttrs):
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

    X_LABEL_AGGREGATE = "xyz.maubot.pr_label_aggregation"


@dataclass
class PullRequestEvent(SerializableAttrs):
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

    @property
    def issue_id(self) -> int:
        return self.pull_request.id

    def meta(self) -> Dict[str, Any]:
        return {
            "pull_request": self.pull_request.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


class PullRequestReviewAction(SerializableEnum):
    SUBMITTED = "submitted"
    EDITED = "edited"
    DISMISSED = "dismissed"


class ReviewState(SerializableEnum):
    COMMENTED = "commented"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Review(SerializableAttrs):
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
class ReviewChanges(SerializableAttrs):
    body: Optional[Change] = None


@dataclass
class PullRequestReviewEvent(SerializableAttrs):
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
class ReviewComment(SerializableAttrs):
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

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id ,
            "node_id": self.node_id,
            "pull_request_review_id": self.pull_request_review_id,
            "commit_id": self.commit_id,
        }


@dataclass
class PullRequestReviewCommentEvent(SerializableAttrs):
    action: PullRequestReviewCommentAction
    pull_request: PartialPullRequest
    comment: ReviewComment
    repository: Repository
    sender: User
    changes: Optional[ReviewChanges] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "pull_request": self.pull_request.meta(),
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


class RepositoryAction(SerializableEnum):
    CREATED = "created"
    DELETED = "deleted"
    ARCHIVED = "archived"
    UNARCHIVED = "unarchived"
    EDITED = "edited"
    RENAMED = "renamed"
    TRANSFERRED = "transferred"
    PUBLICIZED = "publicized"
    PRIVATIZED = "privatized"


@dataclass
class RepositoryEvent(SerializableAttrs):
    action: RepositoryAction
    repository: Repository
    sender: User

    organization: Optional[Organization] = None
    user: Optional[User] = None
    changes: Optional[JSON] = None


class EventType(SerializableEnum):
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PUSH = "push"
    RELEASE = "release"
    STAR = "star"
    WATCH = "watch"
    PING = "ping"
    FORK = "fork"
    CREATE = "create"
    DELETE = "delete"
    META = "meta"
    COMMIT_COMMENT = "commit_comment"
    MILESTONE = "milestone"
    LABEL = "label"
    WIKI = "gollum"
    PUBLIC = "public"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    REPOSITORY = "repository"


Event = Union[IssuesEvent, IssueCommentEvent, PushEvent, ReleaseEvent, StarEvent, WatchEvent,
              PingEvent, ForkEvent, CreateEvent, MetaEvent, CommitCommentEvent, MilestoneEvent,
              LabelEvent, WikiEvent, PublicEvent, PullRequestEvent, PullRequestReviewEvent,
              PullRequestReviewCommentEvent, RepositoryEvent, DeleteEvent]

Action = Union[IssueAction, StarAction, CommentAction, WikiPageAction, MetaAction, ReleaseAction,
               PullRequestAction, PullRequestReviewAction, PullRequestReviewCommentAction,
               MilestoneAction, LabelAction, RepositoryAction]

EVENT_CLASSES = {
    EventType.ISSUES: IssuesEvent,
    EventType.ISSUE_COMMENT: IssueCommentEvent,
    EventType.PUSH: PushEvent,
    EventType.RELEASE: ReleaseEvent,
    EventType.STAR: StarEvent,
    EventType.WATCH: WatchEvent,
    EventType.PING: PingEvent,
    EventType.FORK: ForkEvent,
    EventType.CREATE: CreateEvent,
    EventType.DELETE: DeleteEvent,
    EventType.META: MetaEvent,
    EventType.COMMIT_COMMENT: CommitCommentEvent,
    EventType.MILESTONE: MilestoneEvent,
    EventType.LABEL: LabelEvent,
    EventType.WIKI: WikiEvent,
    EventType.PUBLIC: PublicEvent,
    EventType.PULL_REQUEST: PullRequestEvent,
    EventType.PULL_REQUEST_REVIEW: PullRequestReviewEvent,
    EventType.PULL_REQUEST_REVIEW_COMMENT: PullRequestReviewCommentEvent,
    EventType.REPOSITORY: RepositoryEvent,
}


def expand_enum(enum: Type[SerializableEnum]) -> Dict[str, SerializableEnum]:
    if not enum:
        return {}
    return {field.name: field for field in enum}


ACTION_CLASSES = {
    EventType.ISSUES: IssueAction,
    EventType.STAR: StarAction,
    EventType.COMMIT_COMMENT: CommentAction,
    EventType.ISSUE_COMMENT: CommentAction,
    EventType.PULL_REQUEST: PullRequestAction,
    EventType.PULL_REQUEST_REVIEW: PullRequestReviewAction,
    EventType.PULL_REQUEST_REVIEW_COMMENT: PullRequestReviewCommentAction,
    EventType.WIKI: WikiPageAction,
    EventType.META: MetaAction,
    EventType.RELEASE: ReleaseAction,
    EventType.MILESTONE: MilestoneAction,
    EventType.LABEL: LabelAction,
    EventType.REPOSITORY: RepositoryAction,
}

OTHER_ENUMS = {
    "ReviewState": ReviewState,
}
