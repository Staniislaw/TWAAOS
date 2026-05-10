class TestRegistrations:

    def _create_event(self, client, headers, sample_event_data):
        """Helper — creează eveniment și returnează id"""
        r = client.post("/events/", json=sample_event_data, headers=headers)
        assert r.status_code == 200
        return r.json()["id"]

    def test_register_to_event(self, client, organizer_headers, auth_headers, sample_event_data):
        """Test înregistrare la eveniment"""
        event_id = self._create_event(client, organizer_headers, sample_event_data)
        response = client.post(f"/events/{event_id}/register", headers=auth_headers)
        assert response.status_code == 200
        assert "registration_id" in response.json()

    def test_register_twice_to_same_event(self, client, organizer_headers, auth_headers, sample_event_data):
        """Test înregistrare dublă la același eveniment"""
        event_id = self._create_event(client, organizer_headers, sample_event_data)
        client.post(f"/events/{event_id}/register", headers=auth_headers)
        response = client.post(f"/events/{event_id}/register", headers=auth_headers)
        assert response.status_code == 400

    def test_register_without_auth(self, client, organizer_headers, sample_event_data):
        """Test înregistrare fără autentificare"""
        event_id = self._create_event(client, organizer_headers, sample_event_data)
        response = client.post(f"/events/{event_id}/register")
        assert response.status_code == 401

    def test_register_to_nonexistent_event(self, client, auth_headers):
        """Test înregistrare la eveniment inexistent"""
        response = client.post("/events/999999/register", headers=auth_headers)
        assert response.status_code == 404

    def test_unregister_from_event(self, client, organizer_headers, auth_headers, sample_event_data):
        """Test dezînscriere de la eveniment"""
        event_id = self._create_event(client, organizer_headers, sample_event_data)
        client.post(f"/events/{event_id}/register", headers=auth_headers)
        response = client.delete(f"/events/{event_id}/unregister", headers=auth_headers)
        assert response.status_code == 200

    def test_is_registered_before_and_after(self, client, organizer_headers, auth_headers, sample_event_data):
        """Test endpoint verificare înregistrare înainte și după"""
        event_id = self._create_event(client, organizer_headers, sample_event_data)

        before = client.get(f"/events/{event_id}/is-registered", headers=auth_headers)
        assert before.json()["registered"] == False

        client.post(f"/events/{event_id}/register", headers=auth_headers)

        after = client.get(f"/events/{event_id}/is-registered", headers=auth_headers)
        assert after.json()["registered"] == True