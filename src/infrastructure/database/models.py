"""SQLAlchemy database models for persistence."""
from datetime import datetime
from uuid import UUID
import json
from sqlalchemy import Column, String, DateTime, Integer, Text, TypeDecorator, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, JSON as PG_JSON
from sqlalchemy.orm import declarative_base, relationship, backref

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


class JSONEncodedDict(TypeDecorator):
    """
    Custom type that stores dictionaries as JSON in both SQLite and PostgreSQL.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else {}
        else:
            if value is not None:
                return json.dumps(value)
            return json.dumps({})

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else {}
        else:
            if value is not None:
                return json.loads(value)
            return {}


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
    created_by = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_count = Column(Integer, nullable=False, default=0)
    output_count = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<NotebookModel(id={self.id}, name='{self.name}')>"


class SourceModel(Base):
    """
    SQLAlchemy model for Source entity.

    Maps to the 'sources' table in PostgreSQL.
    Following clean architecture, this is an infrastructure concern.
    """
    __tablename__ = "sources"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    notebook_id = Column(PG_UUID(as_uuid=True), ForeignKey('notebooks.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    source_type = Column(String(20), nullable=False)  # 'file' or 'url'
    file_type = Column(String(20), nullable=True)  # 'pdf', 'docx', 'doc', 'txt', 'md'
    url = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash
    extracted_text = Column(Text, nullable=False, default="")
    source_metadata = Column(JSONEncodedDict, nullable=False, default={})
    created_by = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)

    # Relationship to notebook (optional, for SQLAlchemy ORM queries)
    # Use passive_deletes='all' to let database CASCADE handle deletion
    notebook = relationship("NotebookModel", backref=backref("sources", passive_deletes="all"))

    def __repr__(self):
        return f"<SourceModel(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class OutputModel(Base):
    """
    SQLAlchemy model for Output entity.

    Maps to the 'outputs' table in PostgreSQL.
    Following clean architecture, this is an infrastructure concern.
    """
    __tablename__ = "outputs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    notebook_id = Column(PG_UUID(as_uuid=True), ForeignKey('notebooks.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False, default="")
    output_type = Column(String(50), nullable=False, default="blog_post")
    status = Column(String(20), nullable=False, default="draft")
    prompt = Column(Text, nullable=True)
    template_name = Column(String(100), nullable=True)
    output_metadata = Column(JSONEncodedDict, nullable=False, default={})
    source_references = Column(JSONEncodedList, nullable=False, default=[])
    word_count = Column(Integer, nullable=False, default=0)
    created_by = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to notebook (optional, for SQLAlchemy ORM queries)
    # Use passive_deletes='all' to let database CASCADE handle deletion
    notebook = relationship("NotebookModel", backref=backref("outputs", passive_deletes="all"))

    def __repr__(self):
        return f"<OutputModel(id={self.id}, title='{self.title}', type='{self.output_type}', status='{self.status}')>"
