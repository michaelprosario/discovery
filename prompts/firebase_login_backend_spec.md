# Firebase Authentication Backend Specification

## Overview

This document specifies the implementation of Firebase Authentication for the Discovery FastAPI backend. The implementation will protect all API endpoints and track resource ownership through user email addresses.

**Created:** December 2, 2025  
**Status:** Draft  
**Repository:** michaelprosario/discovery  
**Branch:** feat/firebase-login

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Firebase Authentication Architecture](#firebase-authentication-architecture)
3. [Entity Modifications](#entity-modifications)
4. [Database Schema Changes](#database-schema-changes)
5. [API Security Implementation](#api-security-implementation)
6. [Migration Strategy](#migration-strategy)
7. [Testing Requirements](#testing-requirements)
8. [Implementation Checklist](#implementation-checklist)

---

## Current State Analysis

### FastAPI Application Structure

**Main Application:** `src/api/main.py`
- FastAPI app with CORS enabled for all origins
- No authentication middleware currently implemented
- 7 routers exposed without protection:
  - `/api/notebooks` - Notebook CRUD operations
  - `/api/sources` - Source management
  - `/api/outputs` - Output management
  - `/api/vector-search` - Vector database operations
  - `/api/article-search` - Article search functionality
  - `/api/qa` - Question & Answer operations
  - `/api/mindmap` - Mind map generation

### Existing Entities

#### 1. **Notebook Entity** (`src/core/entities/notebook.py`)
**Current Fields:**
- `id: UUID`
- `name: str`
- `description: Optional[str]`
- `tags: List[str]`
- `created_at: datetime`
- `updated_at: datetime`
- `source_count: int`
- `output_count: int`

**Missing:** `created_by` field for ownership tracking

#### 2. **Source Entity** (`src/core/entities/source.py`)
**Current Fields:**
- `id: UUID`
- `notebook_id: UUID`
- `name: str`
- `source_type: SourceType`
- `file_type: Optional[FileType]`
- `url: Optional[str]`
- `file_path: Optional[str]`
- `file_size: Optional[int]`
- `content_hash: str`
- `extracted_text: str`
- `metadata: Dict[str, Any]`
- `created_at: datetime`
- `updated_at: datetime`
- `deleted_at: Optional[datetime]`

**Missing:** `created_by` field for ownership tracking

#### 3. **Output Entity** (`src/core/entities/output.py`)
**Current Fields:**
- `id: UUID`
- `notebook_id: UUID`
- `title: str`
- `content: str`
- `output_type: OutputType`
- `status: OutputStatus`
- `prompt: Optional[str]`
- `template_name: Optional[str]`
- `metadata: Dict[str, Any]`
- `source_references: list[str]`
- `word_count: int`
- `created_at: datetime`
- `updated_at: datetime`
- `completed_at: Optional[datetime]`

**Missing:** `created_by` field for ownership tracking

### Database Models

**Location:** `src/infrastructure/database/models.py`

Current SQLAlchemy models (`NotebookModel`, `SourceModel`, `OutputModel`) mirror entity structures and also lack the `created_by` field.

### Dependency Injection Pattern

All routers use FastAPI's dependency injection system for:
- Repository instances
- Service instances
- Provider instances

This pattern can be extended to inject authenticated user context.

---

## Firebase Authentication Architecture

### Firebase Admin SDK Integration

**Package:** `firebase-admin`

**Purpose:** 
- Server-side verification of Firebase ID tokens
- No direct user management needed (handled by frontend/Firebase Auth)
- Token validation and email extraction

### Authentication Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Angular   │         │   FastAPI    │         │ Firebase Admin  │
│   Frontend  │         │   Backend    │         │      SDK        │
└──────┬──────┘         └──────┬───────┘         └────────┬────────┘
       │                       │                          │
       │ 1. Login with         │                          │
       │    Firebase Auth      │                          │
       ├──────────────────────>│                          │
       │                       │                          │
       │ 2. Receive ID Token   │                          │
       │<──────────────────────┤                          │
       │                       │                          │
       │ 3. API Request        │                          │
       │    with Bearer Token  │                          │
       ├──────────────────────>│                          │
       │                       │                          │
       │                       │ 4. Verify Token          │
       │                       ├─────────────────────────>│
       │                       │                          │
       │                       │ 5. Decoded Token         │
       │                       │    (with email)          │
       │                       │<─────────────────────────┤
       │                       │                          │
       │                       │ 6. Execute Business      │
       │                       │    Logic with User Email │
       │                       │                          │
       │ 7. Response           │                          │
       │<──────────────────────┤                          │
       │                       │                          │
```

### Configuration Requirements

**Environment Variables:**
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# Or use service account JSON directly
FIREBASE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
```

**Firebase Admin Initialization:**
```python
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
```

---

## Entity Modifications

### 1. Notebook Entity Changes

**File:** `src/core/entities/notebook.py`

**Add Field:**
```python
created_by: str = ""  # Email address of the user who created the notebook
```

**Update `create()` Factory Method:**
```python
@staticmethod
def create(
    name: str,
    created_by: str,  # NEW: Required parameter
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Result['Notebook']:
    """
    Factory method to create a new notebook with validation.

    Args:
        name: Notebook name (required, max 255 chars)
        created_by: Email of the user creating the notebook (required)
        description: Optional description (max 2000 chars)
        tags: Optional list of tags for categorization

    Returns:
        Result[Notebook]: Success with notebook or failure with validation errors
    """
    errors = []

    # Validate name
    name = name.strip() if name else ""
    if not name:
        errors.append(ValidationError(
            field="name",
            message="Name is required and cannot be empty",
            code="REQUIRED"
        ))
    elif len(name) > 255:
        errors.append(ValidationError(
            field="name",
            message="Name cannot exceed 255 characters",
            code="MAX_LENGTH"
        ))

    # Validate created_by (email)
    created_by = created_by.strip() if created_by else ""
    if not created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by (user email) is required",
            code="REQUIRED"
        ))
    elif "@" not in created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by must be a valid email address",
            code="INVALID_FORMAT"
        ))

    # Validate description
    if description and len(description) > 2000:
        errors.append(ValidationError(
            field="description",
            message="Description cannot exceed 2000 characters",
            code="MAX_LENGTH"
        ))

    # Return validation failures if any
    if errors:
        return Result.validation_failure(errors)

    # Create notebook
    notebook = Notebook(
        name=name,
        created_by=created_by,
        description=description,
        tags=tags or []
    )

    return Result.success(notebook)
```

### 2. Source Entity Changes

**File:** `src/core/entities/source.py`

**Add Field:**
```python
created_by: str = ""  # Email address of the user who created the source
```

**Update Factory Methods:**
All three factory methods (`create_file_source()`, `create_url_source()`, `create_text_source()`) need to accept `created_by` parameter:

```python
@staticmethod
def create_file_source(
    notebook_id: UUID,
    name: str,
    file_type: FileType,
    file_size: int,
    content: bytes,
    created_by: str,  # NEW: Required parameter
    metadata: Optional[Dict[str, Any]] = None
) -> Result['Source']:
    # ... existing validation ...
    
    # Validate created_by
    created_by = created_by.strip() if created_by else ""
    if not created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by (user email) is required",
            code="REQUIRED"
        ))
    elif "@" not in created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by must be a valid email address",
            code="INVALID_FORMAT"
        ))
    
    # ... rest of implementation ...
    
    source = Source(
        notebook_id=notebook_id,
        name=name,
        source_type=SourceType.FILE,
        file_type=file_type,
        file_size=file_size,
        content_hash=content_hash,
        created_by=created_by,
        metadata=metadata or {}
    )
```

*Similar changes needed for `create_url_source()` and `create_text_source()`*

### 3. Output Entity Changes

**File:** `src/core/entities/output.py`

**Add Field:**
```python
created_by: str = ""  # Email address of the user who created the output
```

**Update `create()` Factory Method:**
```python
@staticmethod
def create(
    notebook_id: UUID,
    title: str,
    created_by: str,  # NEW: Required parameter
    output_type: OutputType = OutputType.BLOG_POST,
    prompt: Optional[str] = None,
    template_name: Optional[str] = None
) -> Result['Output']:
    """
    Factory method to create a new output with validation.

    Args:
        notebook_id: ID of the parent notebook
        title: Title for the output
        created_by: Email of the user creating the output (required)
        output_type: Type of output (default: BLOG_POST)
        prompt: Optional custom prompt used for generation
        template_name: Optional template name used

    Returns:
        Result[Output]: Success with output or failure with validation errors
    """
    errors = []

    # Validate title
    title = title.strip() if title else ""
    if not title:
        errors.append(ValidationError(
            field="title",
            message="Title is required and cannot be empty",
            code="REQUIRED"
        ))
    elif len(title) > 500:
        errors.append(ValidationError(
            field="title",
            message="Title cannot exceed 500 characters",
            code="MAX_LENGTH"
        ))

    # Validate notebook_id
    if not notebook_id:
        errors.append(ValidationError(
            field="notebook_id",
            message="Notebook ID is required",
            code="REQUIRED"
        ))

    # Validate created_by
    created_by = created_by.strip() if created_by else ""
    if not created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by (user email) is required",
            code="REQUIRED"
        ))
    elif "@" not in created_by:
        errors.append(ValidationError(
            field="created_by",
            message="Created by must be a valid email address",
            code="INVALID_FORMAT"
        ))

    # ... rest of validation ...

    output = Output(
        notebook_id=notebook_id,
        title=title,
        created_by=created_by,
        output_type=output_type,
        prompt=prompt,
        template_name=template_name,
        status=OutputStatus.DRAFT
    )

    return Result.success(output)
```

---

## Database Schema Changes

### 1. Add `created_by` Column to Models

**File:** `src/infrastructure/database/models.py`

**NotebookModel:**
```python
class NotebookModel(Base):
    __tablename__ = "notebooks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSONEncodedList, nullable=False, default=[])
    created_by = Column(String(255), nullable=False, index=True)  # NEW
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_count = Column(Integer, nullable=False, default=0)
    output_count = Column(Integer, nullable=False, default=0)
```

**SourceModel:**
```python
class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    notebook_id = Column(PG_UUID(as_uuid=True), ForeignKey('notebooks.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    name = Column(String(500), nullable=False)
    source_type = Column(String(20), nullable=False)
    file_type = Column(String(20), nullable=True)
    url = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)
    extracted_text = Column(Text, nullable=False, default="")
    source_metadata = Column(JSONEncodedDict, nullable=False, default={})
    created_by = Column(String(255), nullable=False, index=True)  # NEW
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    notebook = relationship("NotebookModel", backref=backref("sources", passive_deletes="all"))
```

**OutputModel:**
```python
class OutputModel(Base):
    __tablename__ = "outputs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    notebook_id = Column(PG_UUID(as_uuid=True), ForeignKey('notebooks.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False, default="")
    output_type = Column(String(50), nullable=False, default="blog_post")
    status = Column(String(20), nullable=False, default="draft")
    prompt = Column(Text, nullable=True)
    template_name = Column(String(100), nullable=True)
    output_metadata = Column(JSONEncodedDict, nullable=False, default={})
    source_references = Column(JSONEncodedList, nullable=False, default=[])
    word_count = Column(Integer, nullable=False, default=0)
    created_by = Column(String(255), nullable=False, index=True)  # NEW
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    notebook = relationship("NotebookModel", backref=backref("outputs", passive_deletes="all"))
```

### 2. Alembic Migration

**Create Migration:**
```bash
alembic revision -m "add_created_by_to_all_tables"
```

**Migration File:** `src/infrastructure/migrations/versions/XXXX_add_created_by_to_all_tables.py`

```python
"""add created_by to all tables

Revision ID: XXXX
Revises: <previous_revision>
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'XXXX'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_by column to notebooks table
    op.add_column('notebooks', 
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_notebooks_created_by', 'notebooks', ['created_by'])
    
    # Add created_by column to sources table
    op.add_column('sources', 
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_sources_created_by', 'sources', ['created_by'])
    
    # Add created_by column to outputs table
    op.add_column('outputs', 
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system@discovery.local')
    )
    op.create_index('ix_outputs_created_by', 'outputs', ['created_by'])
    
    # Remove server defaults after backfilling existing data
    op.alter_column('notebooks', 'created_by', server_default=None)
    op.alter_column('sources', 'created_by', server_default=None)
    op.alter_column('outputs', 'created_by', server_default=None)

def downgrade():
    # Remove created_by columns
    op.drop_index('ix_outputs_created_by', 'outputs')
    op.drop_column('outputs', 'created_by')
    
    op.drop_index('ix_sources_created_by', 'sources')
    op.drop_column('sources', 'created_by')
    
    op.drop_index('ix_notebooks_created_by', 'notebooks')
    op.drop_column('notebooks', 'created_by')
```

---

## API Security Implementation

### 1. Firebase Authentication Middleware

**File:** `src/api/auth/firebase_auth.py` (new file)

```python
"""Firebase authentication dependencies for FastAPI."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
import os
from functools import lru_cache

security = HTTPBearer()

@lru_cache()
def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Uses environment variables for configuration:
    - FIREBASE_CREDENTIALS_PATH: Path to service account JSON file
    - FIREBASE_SERVICE_ACCOUNT_JSON: Direct JSON content (alternative)
    """
    if firebase_admin._apps:
        return  # Already initialized
    
    credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    
    if credentials_path and os.path.exists(credentials_path):
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
    elif service_account_json:
        import json
        cred = credentials.Certificate(json.loads(service_account_json))
        firebase_admin.initialize_app(cred)
    else:
        raise RuntimeError(
            "Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_JSON environment variable."
        )


async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify Firebase ID token and extract user email.
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        str: User's email address from verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    initialize_firebase()
    
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        
        # Extract email from token
        email = decoded_token.get('email')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return email
        
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user_email(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[str]:
    """
    Optional authentication - returns email if token present and valid, None otherwise.
    
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user_email(credentials)
    except HTTPException:
        return None
```

### 2. Update Router Dependencies

**Example: Notebooks Router** (`src/api/notebooks_router.py`)

```python
from .auth.firebase_auth import get_current_user_email

# Existing imports...

@router.post(
    "",
    response_model=NotebookResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Notebook created successfully"},
        400: {"model": ValidationErrorResponse},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse}
    }
)
async def create_notebook(
    request: CreateNotebookRequest,
    current_user_email: str = Depends(get_current_user_email),  # NEW
    service: NotebookManagementService = Depends(get_notebook_service)
) -> NotebookResponse:
    """
    Create a new notebook.
    
    Requires authentication. The notebook will be owned by the authenticated user.
    """
    # Create command with user email
    command = CreateNotebookCommand(
        name=request.name,
        description=request.description,
        tags=request.tags,
        created_by=current_user_email  # NEW
    )
    
    # Execute command
    result = service.create_notebook(command)
    
    # Handle result...
```

**Apply to All Endpoints:**
- All POST/PUT/DELETE endpoints: Require `get_current_user_email`
- GET endpoints for listing user's resources: Require `get_current_user_email`
- GET endpoints for public/shared resources: Use `get_optional_user_email`

### 3. Repository Filtering by User

**Update Query Handlers to Filter by User Email:**

**Example: List Notebooks Query**

```python
# In NotebookRepository
def list_notebooks(
    self,
    created_by: str,  # NEW: Filter by owner
    search: Optional[str] = None,
    tags: Optional[List[str]] = None,
    sort_by: SortOption = SortOption.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: int = 100,
    offset: int = 0
) -> List[Notebook]:
    """List notebooks owned by the specified user."""
    query = self.session.query(NotebookModel).filter(
        NotebookModel.created_by == created_by  # NEW
    )
    
    # Apply existing filters (search, tags, etc.)
    # ...
    
    return query.all()
```

### 4. Authorization Checks

**Add Authorization Helper:** `src/api/auth/authorization.py` (new file)

```python
"""Authorization helpers for resource access control."""
from fastapi import HTTPException, status
from typing import Protocol


class OwnedResource(Protocol):
    """Protocol for resources that have ownership."""
    created_by: str


def require_resource_owner(resource: OwnedResource, user_email: str) -> None:
    """
    Verify that the user owns the resource.
    
    Args:
        resource: Resource with created_by field
        user_email: Email of the authenticated user
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the resource
    """
    if resource.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )


def require_resource_owner_or_fail(
    resource: OwnedResource | None, 
    user_email: str,
    resource_type: str = "Resource"
) -> None:
    """
    Verify resource exists and user owns it.
    
    Args:
        resource: Resource to check (may be None)
        user_email: Email of the authenticated user
        resource_type: Type of resource for error message
        
    Raises:
        HTTPException: 404 if resource not found or not owned by user
    """
    if not resource or resource.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} not found"
        )
```

**Usage in Endpoints:**

```python
from .auth.authorization import require_resource_owner_or_fail

@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: UUID,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
) -> NotebookResponse:
    """Get a notebook by ID. Only the owner can access it."""
    query = GetNotebookByIdQuery(id=notebook_id)
    result = service.get_notebook(query)
    
    if result.is_failure:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    notebook = result.value
    
    # Authorization check
    require_resource_owner_or_fail(notebook, current_user_email, "Notebook")
    
    return NotebookResponse.from_entity(notebook)
```

### 5. Update Command DTOs

**File:** `src/core/commands/notebook_commands.py`

```python
@dataclass
class CreateNotebookCommand:
    """Command to create a new notebook."""
    name: str
    created_by: str  # NEW
    description: Optional[str] = None
    tags: Optional[List[str]] = None
```

*Similar updates needed for Source and Output command classes*

---

## Migration Strategy

### Phase 1: Database Migration
1. Create and test migration locally
2. Backup production database
3. Apply migration to add `created_by` columns with default value
4. Verify data integrity

### Phase 2: Code Updates
1. Update entities with `created_by` field
2. Update database models
3. Update repository methods
4. Update service layer
5. Update command/query objects

### Phase 3: Authentication Layer
1. Install `firebase-admin` package
2. Implement authentication middleware
3. Add authorization helpers
4. Update router dependencies

### Phase 4: Testing
1. Unit tests for entities with `created_by`
2. Integration tests for authentication
3. End-to-end tests for protected endpoints
4. Test authorization rules

### Phase 5: Frontend Integration
1. Configure Firebase in Angular app
2. Implement login/logout UI
3. Add token to HTTP interceptor
4. Handle 401/403 responses
5. Update API calls to include auth header

### Phase 6: Deployment
1. Deploy backend with authentication disabled (feature flag)
2. Deploy frontend with Firebase integration
3. Enable authentication via feature flag
4. Monitor for issues
5. Roll back if necessary

---

## Testing Requirements

### Unit Tests

**Test Entity Creation with `created_by`:**
```python
def test_create_notebook_with_created_by():
    result = Notebook.create(
        name="Test Notebook",
        created_by="user@example.com"
    )
    assert result.is_success
    assert result.value.created_by == "user@example.com"

def test_create_notebook_without_created_by():
    result = Notebook.create(
        name="Test Notebook",
        created_by=""
    )
    assert result.is_failure
    assert any(e.field == "created_by" for e in result.errors)

def test_create_notebook_with_invalid_email():
    result = Notebook.create(
        name="Test Notebook",
        created_by="not-an-email"
    )
    assert result.is_failure
    assert any(e.code == "INVALID_FORMAT" for e in result.errors)
```

### Integration Tests

**Test Authentication Middleware:**
```python
import pytest
from fastapi.testclient import TestClient

def test_protected_endpoint_without_token(client: TestClient):
    response = client.post("/api/notebooks", json={"name": "Test"})
    assert response.status_code == 401

def test_protected_endpoint_with_invalid_token(client: TestClient):
    response = client.post(
        "/api/notebooks",
        json={"name": "Test"},
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token(client: TestClient, mock_firebase_token):
    response = client.post(
        "/api/notebooks",
        json={"name": "Test"},
        headers={"Authorization": f"Bearer {mock_firebase_token}"}
    )
    assert response.status_code == 201
    assert response.json()["created_by"] == "user@example.com"
```

**Test Authorization:**
```python
def test_user_cannot_access_other_users_notebook(
    client: TestClient,
    user1_token: str,
    user2_token: str,
    user1_notebook_id: UUID
):
    # User 2 tries to access User 1's notebook
    response = client.get(
        f"/api/notebooks/{user1_notebook_id}",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 404  # Not found (hiding existence)

def test_user_can_access_own_notebook(
    client: TestClient,
    user1_token: str,
    user1_notebook_id: UUID
):
    response = client.get(
        f"/api/notebooks/{user1_notebook_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(user1_notebook_id)
```

### Test Fixtures

**Mock Firebase Token:**
```python
@pytest.fixture
def mock_firebase_auth(monkeypatch):
    """Mock Firebase auth for testing."""
    def mock_verify_token(token):
        if token == "valid-token":
            return {"email": "user@example.com", "uid": "user123"}
        raise auth.InvalidIdTokenError("Invalid token")
    
    monkeypatch.setattr("firebase_admin.auth.verify_id_token", mock_verify_token)
```

---

## Implementation Checklist

### Dependencies
- [ ] Add `firebase-admin` to `pyproject.toml`
- [ ] Install package: `pip install firebase-admin`

### Database Layer
- [ ] Add `created_by` field to `Notebook` entity
- [ ] Add `created_by` field to `Source` entity
- [ ] Add `created_by` field to `Output` entity
- [ ] Add `created_by` column to `NotebookModel`
- [ ] Add `created_by` column to `SourceModel`
- [ ] Add `created_by` column to `OutputModel`
- [ ] Create Alembic migration
- [ ] Test migration locally
- [ ] Update repository methods to filter by `created_by`

### Authentication Layer
- [ ] Create `src/api/auth/firebase_auth.py`
- [ ] Implement `initialize_firebase()`
- [ ] Implement `get_current_user_email()` dependency
- [ ] Implement `get_optional_user_email()` dependency
- [ ] Create `src/api/auth/authorization.py`
- [ ] Implement `require_resource_owner()` helper
- [ ] Implement `require_resource_owner_or_fail()` helper

### Command/Query Updates
- [ ] Update `CreateNotebookCommand` with `created_by`
- [ ] Update `CreateOutputCommand` with `created_by`
- [ ] Update `ImportFileSourceCommand` with `created_by`
- [ ] Update `ImportUrlSourceCommand` with `created_by`
- [ ] Update `ImportTextSourceCommand` with `created_by`
- [ ] Update all List/Get queries to filter by user

### Router Updates
- [ ] Update `/api/notebooks` endpoints with auth dependencies
- [ ] Update `/api/sources` endpoints with auth dependencies
- [ ] Update `/api/outputs` endpoints with auth dependencies
- [ ] Update `/api/vector-search` endpoints with auth dependencies
- [ ] Update `/api/article-search` endpoints with auth dependencies
- [ ] Update `/api/qa` endpoints with auth dependencies
- [ ] Update `/api/mindmap` endpoints with auth dependencies

### Service Layer Updates
- [ ] Update `NotebookManagementService` to accept `created_by`
- [ ] Update `SourceIngestionService` to accept `created_by`
- [ ] Update `OutputManagementService` to accept `created_by`
- [ ] Update `BlogGenerationService` to accept `created_by`

### Testing
- [ ] Unit tests for entity creation with `created_by`
- [ ] Unit tests for email validation
- [ ] Integration tests for Firebase auth middleware
- [ ] Integration tests for authorization checks
- [ ] Test user isolation (users can't see each other's data)
- [ ] Test migration rollback
- [ ] Load testing with authentication

### Configuration
- [ ] Document Firebase setup in README
- [ ] Create `.env.example` with Firebase variables
- [ ] Set up Firebase project
- [ ] Generate service account credentials
- [ ] Configure environment variables

### Documentation
- [ ] API documentation updates (OpenAPI)
- [ ] Update README with authentication setup
- [ ] Create migration guide for existing users
- [ ] Document authorization model

### Deployment
- [ ] Review security configuration
- [ ] Test in staging environment
- [ ] Plan production deployment
- [ ] Prepare rollback plan
- [ ] Monitor authentication metrics

---

## Security Considerations

### Token Security
- Tokens are verified on every request (no session storage needed)
- Token expiration handled by Firebase (default: 1 hour)
- Revoked tokens are detected by Firebase Admin SDK

### Data Isolation
- All queries filtered by `created_by` email
- Users cannot access other users' resources
- 404 responses prevent user enumeration

### CORS Configuration
- Update CORS to allow only specific origins in production
- Configure proper HTTP headers for security

### Rate Limiting
- Consider implementing rate limiting per user
- Prevent token verification DoS attacks

### Audit Logging
- Log authentication attempts
- Log authorization failures
- Track resource access patterns

---

## Future Enhancements

### Shared Resources
- Add sharing mechanism for notebooks
- Implement read-only vs read-write permissions
- Support team/organization concepts

### Role-Based Access Control
- Add admin role for system management
- Implement viewer/editor/owner roles
- Support custom permissions

### API Keys
- Allow users to generate API keys
- Support programmatic access
- Implement key rotation

### Audit Trail
- Track all resource modifications
- Show user activity history
- Support compliance requirements

---

## References

- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**End of Specification**
