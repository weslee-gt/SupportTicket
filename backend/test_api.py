"""
Automated unit and integration tests for FastAPI Support Ticket Portal REST API.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_tickets():
    response = client.get("/api/tickets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    first_ticket = data[0]
    assert "id" in first_ticket
    assert "title" in first_ticket
    assert "description" in first_ticket
    assert "priority" in first_ticket
    assert "status" in first_ticket
    assert "requesterName" in first_ticket
    assert "createdAt" in first_ticket
    assert "updatedAt" in first_ticket


def test_filter_tickets_by_status():
    response = client.get("/api/tickets?status=Open")
    assert response.status_code == 200
    data = response.json()
    for ticket in data:
        assert ticket["status"] == "Open"


def test_filter_tickets_by_priority():
    response = client.get("/api/tickets?priority=High")
    assert response.status_code == 200
    data = response.json()
    for ticket in data:
        assert ticket["priority"] == "High"


def test_filter_tickets_combined():
    response = client.get("/api/tickets?status=Resolved&priority=Low")
    assert response.status_code == 200
    data = response.json()
    for ticket in data:
        assert ticket["status"] == "Resolved"
        assert ticket["priority"] == "Low"


def test_create_get_update_delete_lifecycle():
    # 1. Create Ticket
    new_ticket_payload = {
        "title": "Automated Test Ticket",
        "description": "This is a test description generated for verification.",
        "priority": "Medium",
        "requesterName": "QA Bot",
    }
    create_res = client.post("/api/tickets", json=new_ticket_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    ticket_id = created_data["id"]
    assert created_data["title"] == new_ticket_payload["title"]
    assert created_data["status"] == "Open"  # Default status
    assert created_data["priority"] == "Medium"
    assert created_data["requesterName"] == "QA Bot"

    # 2. Get Ticket by ID
    get_res = client.get(f"/api/tickets/{ticket_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ticket_id

    # 3. Update Ticket Status & Title
    update_payload = {
        "title": "Automated Test Ticket (Updated)",
        "status": "In Progress",
    }
    update_res = client.patch(f"/api/tickets/{ticket_id}", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Automated Test Ticket (Updated)"
    assert updated_data["status"] == "In Progress"
    assert updated_data["priority"] == "Medium"  # Unchanged

    # 4. Delete Ticket
    delete_res = client.delete(f"/api/tickets/{ticket_id}")
    assert delete_res.status_code == 204

    # 5. Verify 404 after deletion
    get_after_delete = client.get(f"/api/tickets/{ticket_id}")
    assert get_after_delete.status_code == 404


def test_validation_errors():
    # Missing required title
    invalid_payload = {
        "description": "Missing title",
        "priority": "Low",
        "requesterName": "Alice",
    }
    res = client.post("/api/tickets", json=invalid_payload)
    assert res.status_code == 422

    # Whitespace only title
    whitespace_payload = {
        "title": "   ",
        "description": "Valid description",
        "priority": "Low",
        "requesterName": "Alice",
    }
    res = client.post("/api/tickets", json=whitespace_payload)
    assert res.status_code == 422

    # Invalid priority
    invalid_priority_payload = {
        "title": "Valid title",
        "description": "Valid description",
        "priority": "Urgent",  # Invalid enum
        "requesterName": "Alice",
    }
    res = client.post("/api/tickets", json=invalid_priority_payload)
    assert res.status_code == 422


def test_search_tickets_by_text():
    marker = "zq7f3a-search-marker"
    payload = {
        "title": f"Printer jam {marker}",
        "description": "Paper is stuck in tray two",
        "priority": "Low",
        "requesterName": "Search Tester",
    }
    created = client.post("/api/tickets", json=payload).json()

    try:
        # Case-insensitive match on the title
        res = client.get("/api/tickets", params={"q": marker.upper()})
        assert res.status_code == 200
        assert [t["id"] for t in res.json()] == [created["id"]]

        # Description and requester name are searched as well
        by_desc = client.get("/api/tickets", params={"q": "tray two"}).json()
        assert created["id"] in [t["id"] for t in by_desc]
        by_requester = client.get("/api/tickets", params={"q": "search tester"}).json()
        assert created["id"] in [t["id"] for t in by_requester]

        # Search composes with the existing status/priority filters
        assert client.get("/api/tickets", params={"q": marker, "status": "Resolved"}).json() == []

        # No match returns an empty list, not an error
        assert client.get("/api/tickets", params={"q": "no-such-ticket-anywhere"}).json() == []
    finally:
        client.delete(f"/api/tickets/{created['id']}")


if __name__ == "__main__":
    import pytest
    import sys

    print("Running test suite...")
    sys.exit(pytest.main(["-v", "test_api.py"]))
