import uuid

class TestAuthentication:

    def test_login_success(self, client):
        """Test login cu credențiale corecte"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        """Test login cu parolă greșită"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "parolagresita"
        })
        assert response.status_code == 401

    def test_login_wrong_username(self, client):
        """Test login cu username inexistent"""
        response = client.post("/auth/login", json={
            "username": "usercare_nu_exista@test.com",
            "password": "oriceparola"
        })
        assert response.status_code == 401

    def test_register_new_user(self, client):
        """Test înregistrare user nou"""
        unique_email = f"newuser_{uuid.uuid4()}@test.com"
        response = client.post("/auth/register", json={
            "username": unique_email,
            "password": "TestPass123!"
        })
        assert response.status_code in [200, 201]

    def test_register_duplicate_user(self, client):
        """Test înregistrare user duplicat"""
        data = {"username": "duplicate@test.com", "password": "oriceparola"}
        client.post("/auth/register", json=data)
        response = client.post("/auth/register", json=data)
        assert response.status_code == 400

    def test_protected_route_without_token(self, client):
        """Test acces rută protejată fără token"""
        response = client.get("/protected")
        assert response.status_code in [401, 422]

    def test_protected_route_with_token(self, client, auth_headers):
        """Test acces rută protejată cu token valid"""
        response = client.get("/protected", headers=auth_headers)
        assert response.status_code == 200

    def test_protected_route_invalid_token(self, client):
        """Test acces rută protejată cu token invalid"""
        response = client.get("/protected", headers={
            "Authorization": "Bearer token_invalid_total"
        })
        assert response.status_code == 401