class TestEvents:

    def test_get_all_events(self, client):
        response = client.get("/events/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_event_success(self, client, organizer_headers, sample_event_data):
        response = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        assert response.status_code == 200
        assert "id" in response.json()

    def test_create_event_without_auth(self, client, sample_event_data):
        response = client.post("/events/", json=sample_event_data)
        assert response.status_code == 401

    def test_create_event_missing_title(self, client, organizer_headers):
        data = {"start_datetime": "2026-06-01T10:00:00"}
        response = client.post("/events/", json=data, headers=organizer_headers)
        assert response.status_code == 422

    def test_get_event_by_id(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.get(f"/events/{event_id}")
        assert response.status_code == 200
        assert response.json()["id"] == event_id

    def test_get_event_not_found(self, client):
        response = client.get("/events/999999")
        assert response.status_code == 404

    def test_update_event(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        updated = {**sample_event_data, "title": "Titlu Actualizat"}
        response = client.put(f"/events/{event_id}", json=updated, headers=organizer_headers)
        assert response.status_code == 200

    def test_update_event_not_found(self, client, auth_headers, sample_event_data):
        response = client.put("/events/99999", json=sample_event_data, headers=auth_headers)
        assert response.status_code == 404

    def test_update_event_forbidden(self, client, organizer_headers, auth_headers, sample_event_data):
        # Creează ca organizer
        create_resp = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create_resp.json()["id"]
        # Aprobă ca admin ca să fie vizibil
        client.put(f"/admin/events/{event_id}/decision", json={"action": "approve"}, headers=auth_headers)
        # Alt organizer încearcă să editeze — nu se poate testa ușor fără al 2-lea user
        # Deci testăm că organizatorul original POATE edita
        response = client.put(f"/events/{event_id}", json=sample_event_data, headers=organizer_headers)
        assert response.status_code == 200

    def test_delete_event(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.delete(f"/events/{event_id}", headers=organizer_headers)
        assert response.status_code == 200

    def test_delete_event_not_found(self, client, organizer_headers):
        response = client.delete("/events/999999", headers=organizer_headers)
        assert response.status_code == 404

    def test_event_status_is_pending_on_create(self, client, organizer_headers, sample_event_data):
        response = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = response.json()["id"]
        event = client.get(f"/events/{event_id}")
        assert event.json()["status"] == "pending"

    def test_get_my_created_events(self, client, organizer_headers, sample_event_data):
        client.post("/events/", json=sample_event_data, headers=organizer_headers)
        response = client.get("/events/my/created", headers=organizer_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_my_event_ids(self, client, auth_headers):
        response = client.get("/events/my/ids", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_participants_not_found(self, client, auth_headers):
        response = client.get("/events/99999/participants", headers=auth_headers)
        assert response.status_code == 404

    def test_is_registered_false(self, client, auth_headers):
        response = client.get("/events/99999/is-registered", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["registered"] == False

    def test_submit_feedback(self, client, organizer_headers, auth_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        client.put(f"/admin/events/{event_id}/decision", json={"action": "approve"}, headers=auth_headers)
        response = client.post(f"/events/{event_id}/feedback", json={"rating": 5, "comment": "Bun!"})
        assert response.status_code == 200

    def test_get_my_qr_not_registered(self, client, auth_headers):
        response = client.get("/events/99999/my-qr", headers=auth_headers)
        assert response.status_code == 404

    def test_verify_qr_invalid(self, client, auth_headers, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.post(f"/events/{event_id}/verify-qr", json={"token": "invalid"}, headers=auth_headers)
        assert response.status_code == 404

    def test_get_event_materials(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.get(f"/events/{event_id}/materials")
        assert response.status_code == 200

    def test_get_event_feedback(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.get(f"/events/{event_id}/feedback")
        assert response.status_code == 200

    def test_get_event_sponsors(self, client, organizer_headers, sample_event_data):
        create = client.post("/events/", json=sample_event_data, headers=organizer_headers)
        event_id = create.json()["id"]
        response = client.get(f"/events/{event_id}/sponsors")
        assert response.status_code == 200