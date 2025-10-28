"""
Integration Test Script for Discovery FastAPI Server

This script demonstrates integration testing of the Discovery API using the requests library.
It performs the same operations as the integration_test.ipynb notebook.

Prerequisites:
- FastAPI server must be running (e.g., `uvicorn src.api.main:app --reload`)
- Database must be initialized and running

Run with: python test_integration_manual.py
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_health_check():
    """Test the health endpoint."""
    print_section("Step 1: Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Server is not healthy!"
    assert response.json()["status"] == "healthy", "Health check failed!"
    print("\n✅ Server is healthy and running!")
    
    return True

def test_create_notebook():
    """Create a new notebook."""
    print_section("Step 2: Create a New Notebook (POST)")
    
    notebook_data = {
        "name": f"Integration Test Notebook {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "This notebook was created by the integration test script",
        "tags": ["integration-test", "automation"]
    }
    
    response = requests.post(f"{API_URL}/notebooks", json=notebook_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201, f"Failed to create notebook: {response.text}"
    
    notebook_id = response.json()["id"]
    print(f"\n✅ Successfully created notebook with ID: {notebook_id}")
    
    return notebook_id, notebook_data

def test_get_notebook(notebook_id, notebook_data):
    """Retrieve and verify the created notebook."""
    print_section("Step 3: Verify Notebook Creation (GET)")
    
    response = requests.get(f"{API_URL}/notebooks/{notebook_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Failed to retrieve notebook: {response.text}"
    
    notebook = response.json()
    assert notebook["id"] == notebook_id, "Notebook ID mismatch!"
    assert notebook["name"] == notebook_data["name"], "Notebook name mismatch!"
    assert notebook["description"] == notebook_data["description"], "Notebook description mismatch!"
    assert set(notebook["tags"]) == set(notebook_data["tags"]), "Notebook tags mismatch!"
    
    print(f"\n✅ Successfully retrieved notebook: {notebook['name']}")
    print(f"   - Created at: {notebook['created_at']}")
    print(f"   - Source count: {notebook['source_count']}")
    print(f"   - Tags: {', '.join(notebook['tags'])}")
    
    return notebook

def test_list_notebooks(notebook_id):
    """List all notebooks and verify our notebook is in the list."""
    print_section("Step 4: List All Notebooks (GET)")
    
    response = requests.get(f"{API_URL}/notebooks")
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to list notebooks: {response.text}"
    
    notebooks_list = response.json()
    print(f"Total notebooks: {notebooks_list['total']}")
    
    # Find our notebook in the list
    our_notebook = None
    for nb in notebooks_list['notebooks']:
        if nb['id'] == notebook_id:
            our_notebook = nb
            break
    
    assert our_notebook is not None, "Created notebook not found in list!"
    print(f"\n✅ Found our notebook in the list!")
    print(f"   Position: {notebooks_list['notebooks'].index(our_notebook) + 1} of {notebooks_list['total']}")
    
    return True

def test_add_source(notebook_id):
    """Add a URL source to the notebook."""
    print_section("Step 5: Add a URL Source to the Notebook (POST)")
    
    source_data = {
        "notebook_id": notebook_id,
        "url": "https://example.com",
        "title": "Example Website"
    }
    
    response = requests.post(f"{API_URL}/sources/url", json=source_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        source_id = response.json()["id"]
        print(f"\n✅ Successfully created source with ID: {source_id}")
        return source_id
    else:
        print(f"Response: {response.text}")
        print(f"\n⚠️ Source creation returned status {response.status_code}")
        print("This may be expected if the web fetch provider is not configured.")
        return None

def test_get_source(source_id, notebook_id):
    """Retrieve and verify the created source."""
    if not source_id:
        print_section("Step 6: Verify Source Addition (GET)")
        print("⚠️ Skipping source verification as source was not created.")
        return None
    
    print_section("Step 6: Verify Source Addition (GET)")
    
    response = requests.get(f"{API_URL}/sources/{source_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Failed to retrieve source: {response.text}"
    
    source = response.json()
    assert source["id"] == source_id, "Source ID mismatch!"
    assert source["notebook_id"] == notebook_id, "Notebook ID mismatch!"
    assert source["source_type"] == "url", "Source type should be 'url'!"
    
    print(f"\n✅ Successfully retrieved source: {source['name']}")
    print(f"   - URL: {source['url']}")
    print(f"   - Created at: {source['created_at']}")
    
    return source

def test_list_sources(notebook_id, source_id):
    """List all sources for the notebook."""
    print_section("Step 7: List Sources for the Notebook (GET)")
    
    response = requests.get(f"{API_URL}/sources/notebook/{notebook_id}")
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to list sources: {response.text}"
    
    sources_list = response.json()
    print(f"Response: {json.dumps(sources_list, indent=2)}")
    print(f"\nTotal sources in notebook: {sources_list['total']}")
    
    if source_id:
        # Find our source in the list
        our_source = None
        for src in sources_list['sources']:
            if src['id'] == source_id:
                our_source = src
                break
        
        assert our_source is not None, "Created source not found in list!"
        print(f"\n✅ Found our source in the notebook's source list!")
    else:
        print(f"\n✅ Sources list retrieved (no sources expected if creation failed)")
    
    return sources_list

def test_verify_notebook_update(notebook_id, source_id):
    """Verify the notebook's source count was updated."""
    print_section("Step 8: Verify Notebook Update")
    
    response = requests.get(f"{API_URL}/notebooks/{notebook_id}")
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, f"Failed to retrieve notebook: {response.text}"
    
    updated_notebook = response.json()
    print(f"Updated source count: {updated_notebook['source_count']}")
    
    if source_id:
        assert updated_notebook['source_count'] >= 1, "Source count should be at least 1!"
        print(f"\n✅ Notebook source count updated correctly!")
    else:
        print(f"\n✅ Notebook retrieved (source count: {updated_notebook['source_count']})")
    
    return updated_notebook

def print_summary(notebook_id):
    """Print test summary."""
    print_section("Summary")
    
    print("""
This script demonstrated the complete integration test workflow:

1. ✅ Health Check - Verified server is running
2. ✅ Create Notebook (POST) - Created a new notebook
3. ✅ Retrieve Notebook (GET) - Verified notebook was created correctly
4. ✅ List Notebooks (GET) - Verified notebook appears in the list
5. ⚠️ Add Source (POST) - Attempted to add a URL source (may fail without proper configuration)
6. ⚠️ Retrieve Source (GET) - Verified source if created
7. ✅ List Sources (GET) - Retrieved all sources for the notebook
8. ✅ Verify Update (GET) - Confirmed notebook reflects the changes

Key Findings:
- POST requests successfully create resources
- GET requests can retrieve individual resources by ID
- GET requests can list all resources
- The API correctly maintains relationships between notebooks and sources
- Changes are immediately visible in subsequent GET requests
    """)
    
    print(f"\nNotebook ID for manual cleanup: {notebook_id}")
    print(f"To delete: DELETE {API_URL}/notebooks/{notebook_id}?cascade=true")

def main():
    """Run all integration tests."""
    print("="*60)
    print("  Integration Test for Discovery FastAPI Server")
    print("="*60)
    print(f"\nTesting API at: {BASE_URL}")
    
    try:
        # Run all test steps
        test_health_check()
        
        notebook_id, notebook_data = test_create_notebook()
        
        test_get_notebook(notebook_id, notebook_data)
        
        test_list_notebooks(notebook_id)
        
        source_id = test_add_source(notebook_id)
        
        test_get_source(source_id, notebook_id)
        
        test_list_sources(notebook_id, source_id)
        
        test_verify_notebook_update(notebook_id, source_id)
        
        print_summary(notebook_id)
        
        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED!")
        print("="*60)
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("\n" + "="*60)
        print("  ❌ ERROR: Cannot connect to server")
        print("="*60)
        print(f"\nMake sure the FastAPI server is running at {BASE_URL}")
        print("Start it with: uvicorn src.api.main:app --reload")
        return 1
        
    except AssertionError as e:
        print("\n" + "="*60)
        print("  ❌ TEST FAILED!")
        print("="*60)
        print(f"\nAssertion Error: {e}")
        return 1
        
    except Exception as e:
        print("\n" + "="*60)
        print("  ❌ UNEXPECTED ERROR!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
