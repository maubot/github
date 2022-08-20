# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2022 Sumner Evans
# Copyright (C) 2022 Tulir Asokan
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
from typing import List, NamedTuple, Optional
import logging as log

from sqlalchemy import Column, String, Text, ForeignKeyConstraint, or_, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

from mautrix.types import UserID, EventID, RoomID

Base = declarative_base()


class MatrixMessage(Base):
    __tablename__ = "matrix_message"

    message_id: str = Column(String(255), primary_key=True)
    room_id: RoomID = Column(String(255), primary_key=True)
    event_id: EventID = Column(String(255), nullable=False)


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    def get_event(self, message_id: str, room_id: RoomID) -> Optional[EventID]:
        s: Session = self.Session()
        event = s.query(MatrixMessage).get((message_id, room_id))
        return event.event_id if event else None

    def put_event(
        self, message_id: str, room_id: RoomID, event_id: EventID, merge: bool = False
    ) -> None:
        s: Session = self.Session()
        evt = MatrixMessage(message_id=message_id, room_id=room_id, event_id=event_id)
        if merge:
            s.merge(evt)
        else:
            s.add(evt)
        s.commit()
