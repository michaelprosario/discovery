# Add Sources by Search Feature

## Overview
This feature allows users to add multiple sources to a notebook by simply entering a search phrase or question. The system searches for relevant articles and automatically adds them as URL sources to the notebook.

## Implementation Details

### Components Created
- **AddSourceBySearch Component** (`/discoveryPortal/src/app/add-source-by-search/`)
  - TypeScript: `add-source-by-search.ts`
  - Template: `add-source-by-search.html`
  - Styles: `add-source-by-search.scss`

### Route Configuration
- Route added: `edit-notebook/:id/add-source-by-search`
- Component: `AddSourceBySearch`
- Protected by: `authGuard`

### User Interface
1. **Search Form**
   - Search phrase/question input field
   - Max results selector (1-10 articles)
   - Search button triggers the API call

2. **Loading State**
   - Displays spinner with informative message
   - Disables form inputs during search

3. **Results Display**
   - Summary card showing:
     - Search phrase used
     - Total articles found
     - Successfully added count
     - Failed count (if any)
   - Detailed article list showing:
     - Article title
     - Article URL (clickable)
     - Success/failure status icon
     - Error message (if failed)
     - Source ID (if successful)

### API Integration
The component uses the existing `SourceApiService.addSourcesBySearch()` method which calls the `/sources/search-and-add` endpoint.

**Request:**
```typescript
{
  notebook_id: string;
  search_phrase: string;
  max_results: number;  // 1-10
}
```

**Response:**
```typescript
{
  notebook_id: string;
  search_phrase: string;
  results: Array<{
    title: string;
    url: string;
    source_id: string | null;
    success: boolean;
    error: string | null;
  }>;
  total_found: number;
  total_added: number;
}
```

## User Flow

### Given
- User is viewing a notebook in the edit-notebook page

### When
1. User clicks "Add Sources by Search" button
2. Navigates to the search page
3. Enters a search phrase (e.g., "machine learning best practices")
4. Optionally adjusts max results (default: 5)
5. Clicks "Search and Add Sources"

### Then
- System displays loading indicator
- Backend searches for relevant articles
- Backend attempts to add each article as a URL source
- Results page displays:
  - Summary of operation
  - List of all articles found
  - Status of each article (success/failure)
  - Any error messages

### User Actions After Search
- **Search Again**: Clears results and allows new search
- **Done**: Returns to notebook edit page

## Features

### Success Indicators
- ✅ Green checkmark for successfully added sources
- Count of successfully added sources
- Source ID displayed for reference

### Error Handling
- ❌ Red X for failed sources
- Detailed error message for each failure
- Validation errors shown before API call
- Network error handling with user-friendly messages

### Accessibility
- Responsive design (mobile, tablet, desktop)
- Proper form labels
- Disabled states for loading
- Clear status indicators

## Testing the Feature

### Prerequisites
1. Backend API running on `http://localhost:8000`
2. Angular app running (or built and served)
3. Valid authentication credentials

### Test Steps
1. Login to the application
2. Open or create a notebook
3. Click "Add Sources by Search" button
4. Enter a search phrase (e.g., "Python programming")
5. Set max results to 3
6. Click "Search and Add Sources"
7. Verify:
   - Loading state appears
   - Results page displays after search completes
   - Articles are listed with proper status
   - Successfully added sources appear in the notebook
   - Error messages are clear (if any failures)
8. Click "Done" to return to notebook

### Edge Cases to Test
- Empty search phrase (should show validation error)
- Max results < 1 or > 10 (should show validation error)
- Network error (should show error message)
- All articles fail to add (should show failure count)
- Some articles succeed, some fail (should show both counts)

## Files Modified

1. **New Files Created:**
   - `/discoveryPortal/src/app/add-source-by-search/add-source-by-search.ts`
   - `/discoveryPortal/src/app/add-source-by-search/add-source-by-search.html`
   - `/discoveryPortal/src/app/add-source-by-search/add-source-by-search.scss`

2. **Modified Files:**
   - `/discoveryPortal/src/app/app.routes.ts` - Added route configuration
   - `/discoveryPortal/src/app/edit-notebook/edit-notebook.html` - Added navigation button

## Related Backend Code
- API Endpoint: `/sources/search-and-add` in `src/api/sources_router.py`
- Service: `ArticleSearchService` in `src/core/services/article_search_service.py`
- Service: `SourceIngestionService` in `src/core/services/source_ingestion_service.py`

## Bug Fixes

### Issue: Missing `created_by` Parameter
**Symptom:** When searching for sources, all articles failed with error:
```
ImportUrlSourceCommand.__init__() missing 1 required positional argument: 'created_by'
```

**Root Cause:** The `/search-and-add` endpoint was not capturing the authenticated user's email and passing it to the `ImportUrlSourceCommand`.

**Fix Applied:** Added `current_user_email: str = Depends(get_current_user_email)` dependency to the endpoint and passed it to the command:
```python
import_command = ImportUrlSourceCommand(
    notebook_id=request.notebook_id,
    title=article.title,
    url=article.link,
    created_by=current_user_email  # Added this line
)
```

**Files Modified:**
- `/src/api/sources_router.py` - Added user authentication dependency and parameter

## Notes
- The backend uses an article search service to find relevant content
- Each found article is automatically imported as a URL source
- The feature respects the max_results limit (1-10 articles)
- Partial success is possible (some articles added, some failed)
- All operations are idempotent - re-searching won't duplicate sources
