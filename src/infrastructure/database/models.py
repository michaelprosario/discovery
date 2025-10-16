"""SQLAlchemy database models for persistence."""
from datetime import datetime
from uuid import UUID
import json
from sqlalchemy import Column, String, DateTime, Integer, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JSONEncodedList(TypeDecorator):
    """
    Custom type that stores lists as JSON strings in SQLite
    and as ARRAY in PostgreSQL for compatibility.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        else:
            if value is not None:
                return json.dumps(value)
            return json.dumps([])

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        else:
            if value is not None:
                return json.loads(value)
            return []


class NotebookModel(Base):
    """
    SQLAlchemy model for Notebook entity.

    Maps to the 'notebooks' table in PostgreSQL.
    Following clean architecture, this is an infrastructure concern.
    """
    __tablename__ = "notebooks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSONEncodedList, nullable=False, default=[])
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_count = Column(Integer, nullable=False, default=0)
    output_count = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<NotebookModel(id={self.id}, name='{self.name}')>"
