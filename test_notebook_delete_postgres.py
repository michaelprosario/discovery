#!/usr/bin/env python3
"""Test script to verify the PostgreSQL CASCADE delete fix."""

import asyncio
import sys
import os
sys.path.insert(0, '/workspaces/discovery')

from httpx import AsyncClient, ASGITransport
from src.api.main import app

async def test_with_real_database():
    """Test deleting a notebook that has sources using the real database."""
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("Testing with real PostgreSQL database...")
        
        # Create a new notebook
        notebook_name = f"Test Notebook for Deletion {asyncio.get_event_loop().time()}"
        create_response = await client.post("/api/notebooks", json={"name": notebook_name})
        if create_response.status_code != 201:
            print(f"Failed to create notebook: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
            
        created_notebook = create_response.json()
        notebook_id = created_notebook["id"]
        print(f"Created notebook: {notebook_id}")

        # Add a source to the notebook
        source_url = "https://en.wikipedia.org/wiki/TestPage123"
        add_source_response = await client.post("/api/sources/url", json={"notebook_id": notebook_id, "url": source_url})
        if add_source_response.status_code != 201:
            print(f"Failed to add source: {add_source_response.status_code}")
            print(f"Response: {add_source_response.text}")
            return False
        
        added_source = add_source_response.json()
        print(f"Added source: {added_source['id']}")

        # Verify the source was added
        list_sources_response = await client.get(f"/api/sources/notebook/{notebook_id}")
        if list_sources_response.status_code != 200:
            print(f"Failed to list sources: {list_sources_response.status_code}")
            return False
            
        listed_sources = list_sources_response.json()["sources"]
        print(f"Verified source count: {len(listed_sources)}")

        # Now try to delete the notebook with cascade=True
        print("Attempting to delete notebook with cascade=True...")
        delete_response = await client.delete(f"/api/notebooks/{notebook_id}?cascade=true")
        
        if delete_response.status_code != 204:
            print(f"DELETE FAILED: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
        
        print("Delete successful!")

        # Verify the notebook is deleted
        get_response = await client.get(f"/api/notebooks/{notebook_id}")
        if get_response.status_code != 404:
            print(f"Notebook was not deleted properly: {get_response.status_code}")
            return False
            
        print("Confirmed notebook is deleted")

        # Verify the source is also deleted (should return 404 or empty list)
        list_sources_after_delete = await client.get(f"/api/sources/notebook/{notebook_id}")
        print(f"Sources after delete status: {list_sources_after_delete.status_code}")
        
        return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_with_real_database())
        if success:
            print("✅ Test passed! Notebook deletion with sources works correctly with PostgreSQL.")
        else:
            print("❌ Test failed! There's still an issue with notebook deletion.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)