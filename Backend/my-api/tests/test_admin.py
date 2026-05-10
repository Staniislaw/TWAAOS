# tests/test_admin.py
import pytest
from datetime import datetime
from database import models
from tests.conftest import TestingSessionLocal


# ✅ Funcție liberă, NU în clasă
def create_pending_event(sample_event_data, organizer_id=1):
    db = TestingSessionLocal()
    try:
        event = models.Event(
            title=sample_event_data["title"],
            description=sample_event_data["description"],
            category=sample_event_data["category"],
            faculty=sample_event_data["faculty"],
            start_datetime=datetime.fromisoformat(sample_event_data["start_datetime"]),
            end_datetime=datetime.fromisoformat(sample_event_data["end_datetime"]),
            location=sample_event_data["location"],
            participation_mode=sample_event_data["participation_mode"],
            entry_type=sample_event_data["entry_type"],
            max_participants=sample_event_data["max_participants"],
            status="pending",
            organizer_id=organizer_id,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event.id
    finally:
        db.close()


class TestAdmin:

    def test_get_all_users_as_admin(self, client, auth_headers):
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_all_users_forbidden_for_non_admin(self, client, organizer_headers):
        response = client.get("/admin/users", headers=organizer_headers)
        assert response.status_code == 403

    def test_get_all_users_unauthorized(self, client):
        response = client.get("/admin/users")
        assert response.status_code == 401  # ✅ fix

    def test_update_user_role(self, client, auth_headers):
        users = client.get("/admin/users", headers=auth_headers).json()
        user_id = users[0]["id"]
        response = client.put(
            f"/admin/users/{user_id}/role",
            json={"role": "organizer"},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_update_user_role_invalid(self, client, auth_headers):
        users = client.get("/admin/users", headers=auth_headers).json()
        user_id = users[0]["id"]
        response = client.put(
            f"/admin/users/{user_id}/role",
            json={"role": "superadmin"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_toggle_user_active(self, client, auth_headers):
        users = client.get("/admin/users", headers=auth_headers).json()
        user_id = users[0]["id"]
        response = client.put(
            f"/admin/users/{user_id}/toggle-active",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "is_active" in response.json()

    def test_get_pending_events(self, client, auth_headers):
        response = client.get("/admin/events/pending", headers=auth_headers)
        assert response.status_code == 200

    def test_get_rejected_events(self, client, auth_headers):
        response = client.get("/admin/events/rejected", headers=auth_headers)
        assert response.status_code == 200

    def test_decide_event_invalid_action(self, client, auth_headers, sample_event_data):
        event_id = create_pending_event(sample_event_data)  # ✅ fără self.
        response = client.put(
            f"/admin/events/{event_id}/decision",
            json={"action": "invalid_action"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_decide_event_approve(self, client, auth_headers, sample_event_data):
        event_id = create_pending_event(sample_event_data)
        response = client.put(
            f"/admin/events/{event_id}/decision",
            json={"action": "approve"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "aprobat" in response.json()["message"]

    def test_decide_event_reject_without_reason(self, client, auth_headers, sample_event_data):
        event_id = create_pending_event(sample_event_data)
        response = client.put(
            f"/admin/events/{event_id}/decision",
            json={"action": "reject"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_decide_event_reject_with_reason(self, client, auth_headers, sample_event_data):
        event_id = create_pending_event(sample_event_data)
        response = client.put(
            f"/admin/events/{event_id}/decision",
            json={"action": "reject", "rejection_reason": "Nu respectă regulamentul"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "respins" in response.json()["message"]

    def test_get_reports(self, client, auth_headers):
        response = client.get("/admin/reports", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "general" in data
        assert "events_per_month" in data

    def test_decide_event_not_found(self, client, auth_headers):
        response = client.put(
            "/admin/events/99999/decision",
            json={"action": "approve"},
            headers=auth_headers
        )
        assert response.status_code == 404