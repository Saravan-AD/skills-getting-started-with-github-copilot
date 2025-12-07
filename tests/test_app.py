import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivities:
    """Test suite for getting activities"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_contain_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_not_empty(self):
        """Test that activities list is not empty"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0


class TestSignup:
    """Test suite for signup functionality"""

    def test_signup_valid_activity_and_email(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_invalid_activity_returns_404(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up twice with same email returns 400"""
        email = "duplicate@example.com"

        # First signup
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200

        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_updates_participants_list(self):
        """Test that signup adds participant to activity"""
        email = "participant@example.com"

        # Get initial participants count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])

        # Sign up
        client.post(f"/activities/Chess Club/signup?email={email}")

        # Verify participant was added
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()["Chess Club"]["participants"]


class TestUnregister:
    """Test suite for unregister functionality"""

    def test_unregister_valid_activity_and_email(self):
        """Test successful unregister from an activity"""
        email = "unregister@example.com"

        # Sign up first
        client.post(f"/activities/Chess Club/signup?email={email}")

        # Then unregister
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_invalid_activity_returns_404(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_non_registered_email_returns_400(self):
        """Test unregister for student not signed up returns 400"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from activity"""
        email = "removetest@example.com"

        # Sign up
        client.post(f"/activities/Chess Club/signup?email={email}")

        # Verify signed up
        response1 = client.get("/activities")
        assert email in response1.json()["Chess Club"]["participants"]

        # Unregister
        client.post(f"/activities/Chess Club/unregister?email={email}")

        # Verify removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Chess Club"]["participants"]


class TestRoot:
    """Test suite for root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that GET / redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
