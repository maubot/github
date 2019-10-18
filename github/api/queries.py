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

GET_REPO_INFO = """
query ($owner: String!, $name: String!) {
    repository(name: $name, owner: $owner) {
        id
    }
}
"""

CREATE_ISSUE = """
mutation ($input: CreateIssueInput!) {
    createIssue(input: $input) {
        issue {
            number
            url
        }
    }
}
"""
