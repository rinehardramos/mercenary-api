"""
End-to-end tests for authentication endpoints.
"""

import pytest
import httpx
import os

BASE_URL = os.environ.get("API_URL", "https://mercenary-api-production.up.railway.app")


@pytest.fixture
def client():
    """HTTP client fixture."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def test_user():
    """Test user data."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_{unique_id}@testmerc.com",
        "password": "TestP@ssw0rd123",
        "display_name": f"Test User {unique_id}"
    }


class TestHealthCheck:
    """Test health endpoint."""
    
    def test_health_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSignup:
    """Test signup endpoint."""
    
    def test_signup_new_user_success(self, client, test_user):
        """Should create a new user successfully."""
        response = client.post(
            "/auth/signup",
            json=test_user
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["requires_verification"] == True
    
    def test_signup_duplicate_email_fails(self, client, test_user):
        """Should fail when signing up with duplicate email."""
        # First signup
        client.post("/auth/signup", json=test_user)
        
        # Second signup with same email
        response = client.post(
            "/auth/signup",
            json=test_user
        )
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    def test_signup_invalid_email_fails(self, client):
        """Should fail with invalid email format."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "not-an-email",
                "password": "password123"
            }
        )
        assert response.status_code == 422
    
    def test_signup_missing_password_fails(self, client):
        """Should fail when password is missing."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422


class TestLogin:
    """Test login endpoint."""
    
    def test_login_success(self, client, test_user):
        """Should login successfully with correct credentials."""
        # First create user
        client.post("/auth/signup", json=test_user)
        
        # Then login
        response = client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    def test_login_wrong_password_fails(self, client, test_user):
        """Should fail with wrong password."""
        # Create user
        client.post("/auth/signup", json=test_user)
        
        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()
    
    def test_login_nonexistent_user_fails(self, client):
        """Should fail when user doesn't exist."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()


class TestProtectedEndpoints:
    """Test protected endpoints with authentication."""
    
    def test_get_me_with_valid_token(self, client, test_user):
        """Should get current user with valid token."""
        # Create user
        signup_response = client.post("/auth/signup", json=test_user)
        token = signup_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["display_name"] == test_user["display_name"]
    
    def test_get_me_without_token_fails(self, client):
        """Should fail without authentication token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_get_me_with_invalid_token_fails(self, client):
        """Should fail with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_get_wallet_balance_authenticated(self, client, test_user):
        """Should get wallet balance with valid token."""
        # Create user
        signup_response = client.post("/auth/signup", json=test_user)
        token = signup_response.json()["access_token"]
        
        # Get balance
        response = client.get(
            "/wallet/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert data["balance"] >= 0


class TestAgents:
    """Test agents endpoint."""
    
    def test_list_agents_no_auth_required(self, client):
        """Should list agents without authentication."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have seeded agents
        assert len(data) >= 5
        
        # Check agent structure
        agent = data[0]
        assert "nickname" in agent
        assert "model_id" in agent
        assert "provider" in agent
        assert "specialization" in agent
        assert "cost_per_task" in agent
    
    def test_get_specific_agent(self, client):
        """Should get a specific agent by nickname."""
        response = client.get("/agents/Shadow")
        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "Shadow"
        assert data["provider"] == "anthropic"
        assert data["specialization"] == "coding"
    
    def test_get_nonexistent_agent_fails(self, client):
        """Should fail when agent doesn't exist."""
        response = client.get("/agents/NonExistentAgent")
        assert response.status_code == 404


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_returns_service_info(self, client):
        """Root endpoint should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Agent Mercenaries Marketplace"
        assert "version" in data
        assert data["docs"] == "/docs"
