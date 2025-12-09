# API Key Authentication Implementation

This implementation adds dual authentication support to the Discovery API, allowing both Firebase ID tokens (primary) and static API key (fallback) authentication.

## Summary of Changes

### 1. Authentication Layer (`src/api/auth/firebase_auth.py`)

Added new authentication function:
- `get_current_user_email_with_api_key()`: Attempts Firebase authentication first, falls back to API key validation
- System user email constant: `api_key_user@system` for API key authenticated requests

### 2. Authorization Layer (`src/api/auth/authorization.py`)

Updated authorization functions to support system user:
- `require_resource_owner()`: System user bypasses ownership checks
- `require_resource_owner_or_fail()`: System user has full access to all resources
- Added `SYSTEM_USER_EMAIL` constant

### 3. Environment Configuration (`.env.example`)

Added configuration for static API key:
```env
# Static API Key for Backend Authentication (alternative to Firebase)
# Generate a secure key using: python -c "import secrets; print(secrets.token_urlsafe(32))"
# STATIC_API_KEY=your-secure-api-key-here
```

### 4. Deployment Documentation (`DEPLOYMENT_GUIDE.md`)

Added section on static API key authentication including:
- How to generate secure API keys
- Local development setup
- Cloud Run deployment with Google Secret Manager
- Usage examples with curl
- Security best practices

### 5. Router Updates

Updated all major API routers to use dual authentication:

#### Vector Search Router (`src/api/vector_search_router.py`)
- `ingest_notebook` - Ingest notebook content into vector database
- `search_similar_content` - Search for similar content
- `get_vector_count` - Get vector count
- `delete_notebook_vectors` - Delete vectors
- `create_collection` - Create vector collection

#### QA Router (`src/api/qa_router.py`)
- `ask_question` - Ask questions about notebook content using RAG

#### Mind Map Router (`src/api/mindmap_router.py`)
- `generate_mindmap` - Generate mind map from notebook
- `get_mindmap_viewer` - Get mind map viewer HTML

#### Article Search Router (`src/api/article_search_router.py`)
- `search_articles` - Search for articles

#### Sources Router (`src/api/sources_router.py`)
All endpoints updated:
- `import_file_source`, `import_url_source`, `import_text_source` - Import sources
- `get_source` - Get source by ID
- `list_sources_by_notebook` - List notebook sources
- `rename_source`, `delete_source`, `restore_source` - Manage sources
- `extract_content` - Extract content from source
- `get_source_preview` - Get source preview
- `add_sources_by_search` - Add sources via search

#### Notebooks Router (`src/api/notebooks_router.py`)
All 9 endpoints updated:
- `create_notebook`, `get_notebook`, `list_notebooks` - CRUD operations
- `update_notebook`, `rename_notebook`, `delete_notebook` - Modifications
- `add_tags`, `remove_tags` - Tag management
- `generate_blog_post` - Generate blog post from notebook

Note: System user can see ALL notebooks in list_notebooks endpoint

#### Outputs Router (`src/api/outputs_router.py`)
All 7 endpoints updated for output management

## How Authentication Works

### Priority Order
1. **Firebase ID Token** (primary): Checks Bearer token from Authorization header
2. **Static API Key** (fallback): Checks X-API-Key header against STATIC_API_KEY env var

### System User Privileges
When authenticated with API key:
- Email: `api_key_user@system`
- Access: Full admin-like access to all resources
- Ownership checks: Bypassed for all operations
- Can view, create, update, and delete any resource

### Usage Examples

#### Using Firebase Authentication
```bash
curl -H "Authorization: Bearer <firebase-id-token>" \
  https://api.example.com/api/notebooks
```

#### Using API Key Authentication
```bash
curl -H "X-API-Key: your-api-key-here" \
  https://api.example.com/api/notebooks
```

## Security Considerations

1. **API Key Storage**: Store in environment variables or secret management systems
2. **Key Rotation**: Rotate API keys periodically
3. **HTTPS Only**: Always use HTTPS in production
4. **Full Access**: API key grants system-level access to all resources
5. **Logging**: Consider logging API key usage for audit trails

## Testing

Run the test script to verify implementation:
```bash
python test_api_key_auth.py
```

## Migration Notes

- Existing Firebase authentication continues to work unchanged
- No breaking changes to existing API contracts
- API key authentication is opt-in (requires STATIC_API_KEY to be set)
- Without STATIC_API_KEY configured, only Firebase auth works
