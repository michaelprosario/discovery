"""Quick script to verify API endpoints work."""
import sys

# Add src to path
sys.path.insert(0, '/workspaces/discovery')

from fastapi.testclient import TestClient
from src.api.main import app

# Create test client
from starlette.testclient import TestClient as StarletteTestClient
client = StarletteTestClient(app)


def test_api():
    """Test basic API functionality."""
    print("Testing Discovery API...\n")

    # Test root endpoint
    print("1. Testing root endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    print(f"   ✓ Root: {response.json()}\n")

    # Test health check
    print("2. Testing health check...")
    response = client.get("/health")
    assert response.status_code == 200
    print(f"   ✓ Health: {response.json()}\n")

    # Test create notebook
    print("3. Testing create notebook...")
    response = client.post(
        "/api/notebooks",
        json={
            "name": "Test Notebook",
            "description": "A test notebook",
            "tags": ["test", "demo"]
        }
    )
    assert response.status_code == 201
    notebook = response.json()
    notebook_id = notebook["id"]
    print(f"   ✓ Created notebook: {notebook['name']} (ID: {notebook_id})\n")

    # Test get notebook
    print("4. Testing get notebook...")
    response = client.get(f"/api/notebooks/{notebook_id}")
    assert response.status_code == 200
    print(f"   ✓ Retrieved notebook: {response.json()['name']}\n")

    # Test list notebooks
    print("5. Testing list notebooks...")
    response = client.get("/api/notebooks")
    assert response.status_code == 200
    data = response.json()
    print(f"   ✓ Found {data['total']} notebook(s)\n")

    # Test update notebook
    print("6. Testing update notebook...")
    response = client.put(
        f"/api/notebooks/{notebook_id}",
        json={"description": "Updated description"}
    )
    assert response.status_code == 200
    print(f"   ✓ Updated notebook\n")

    # Test add tags
    print("7. Testing add tags...")
    response = client.post(
        f"/api/notebooks/{notebook_id}/tags",
        json={"tags": ["new-tag"]}
    )
    assert response.status_code == 200
    notebook = response.json()
    print(f"   ✓ Tags: {notebook['tags']}\n")

    # Test delete notebook
    print("8. Testing delete notebook...")
    response = client.delete(f"/api/notebooks/{notebook_id}")
    assert response.status_code == 204
    print(f"   ✓ Deleted notebook\n")

    # Verify deletion
    print("9. Verifying deletion...")
    response = client.get(f"/api/notebooks/{notebook_id}")
    assert response.status_code == 404
    print(f"   ✓ Notebook not found (as expected)\n")

    print("=" * 60)
    print("✅ All API tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_api()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
