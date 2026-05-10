class TestUsers:

    def test_get_all_users(self, client):
        """Test preluare listă useri"""
        response = client.get("/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_user_by_id(self, client):
        """Test preluare user după ID"""
        response = client.get("/users/1")
        assert response.status_code in [200, 404]

    def test_admin_get_users(self, client, auth_headers):
        """Test admin poate vedea toți userii"""
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_admin_update_role(self, client, auth_headers):
        """Test admin poate schimba rolul unui user"""
        users = client.get("/admin/users", headers=auth_headers).json()
        assert len(users) > 0
        user_id = users[0]["id"]
        response = client.put(
            f"/admin/users/{user_id}/role",
            json={"role": "organizer"},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_admin_invalid_role(self, client, auth_headers):
        response = client.put(
            "/admin/users/7/role",
            json={"role": "superuser_invalid"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_non_admin_cannot_access_admin(self, client):
        """Test user normal nu poate accesa rute admin"""
        response = client.get("/admin/users")
        assert response.status_code in [401, 422]