import pytest
from datetime import datetime
from app.services.user_service import UserService
from app.database.mongodb import mongo_db


@pytest.mark.usefixtures("init_database")
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_service = UserService()

    def test_create_user(self):
        user_data = {
            "user_id": "new_test_user",
            "first_name": "New",
            "last_name": "User",
        }
        user = self.user_service.create_user(user_data)
        assert user is not None
        assert user.user_id == "new_test_user"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.successful_reports == 0
        assert isinstance(user.last_request, datetime)

    def test_get_user(self):
        # First, create a user to retrieve
        user_data = {
            "user_id": "test_user",
            "first_name": "Test",
            "last_name": "User",
        }
        self.user_service.create_user(user_data)

        user = self.user_service.get_user("test_user")
        assert user is not None
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_update_user(self):
        # First, create a user to update
        user_data = {
            "user_id": "update_test_user",
            "first_name": "Update",
            "last_name": "User",
        }
        self.user_service.create_user(user_data)

        updated_data = {"first_name": "Updated"}
        updated_user = self.user_service.update_user("update_test_user", updated_data)
        assert updated_user is not None
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "User"  # Ensure last_name is unchanged

    def test_update_successful_reports(self):
        user_data = {
            "user_id": "report_test_user",
            "first_name": "Report",
            "last_name": "User",
        }
        user = self.user_service.create_user(user_data)
        assert user.successful_reports == 0

        updated_user = self.user_service.update_user(
            "report_test_user", {"successful_reports": 1}
        )
        assert updated_user.successful_reports == 1

    def test_update_last_request(self):
        user_data = {
            "user_id": "request_test_user",
            "first_name": "Request",
            "last_name": "User",
        }
        user = self.user_service.create_user(user_data)
        original_last_request = user.last_request

        # Wait a short time to ensure the timestamp changes
        import time

        time.sleep(0.1)

        updated_user = self.user_service.update_user(
            "request_test_user", {"last_request": datetime.now()}
        )
        assert updated_user.last_request > original_last_request

    def teardown_method(self):
        mongo_db.db.users.delete_many({})


if __name__ == "__main__":
    pytest.main()
