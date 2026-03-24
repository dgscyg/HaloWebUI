from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestAuths(AbstractPostgresTest):
    BASE_PATH = "/api/v1/auths"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.auths import Auths
        from open_webui.models.users import Users

        cls.users = Users
        cls.auths = Auths

    def test_get_session_user(self):
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url(""))
        assert response.status_code == 200
        assert response.json() == {
            "id": "1",
            "name": "John Doe",
            "email": "john.doe@openwebui.com",
            "role": "user",
            "profile_image_url": "/user.png",
        }

    def test_update_profile(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("old_password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )

        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(
                self.create_url("/update/profile"),
                json={"name": "John Doe 2", "profile_image_url": "/user2.png"},
            )
        assert response.status_code == 200
        db_user = self.users.get_user_by_id(user.id)
        assert db_user.name == "John Doe 2"
        assert db_user.profile_image_url == "/user2.png"

    def test_update_password(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("old_password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )

        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(
                self.create_url("/update/password"),
                json={"password": "old_password", "new_password": "new_password"},
            )
        assert response.status_code == 200

        old_auth = self.auths.authenticate_user(
            "john.doe@openwebui.com", "old_password"
        )
        assert old_auth is None
        new_auth = self.auths.authenticate_user(
            "john.doe@openwebui.com", "new_password"
        )
        assert new_auth is not None

    def test_signin(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )
        response = self.fast_api_client.post(
            self.create_url("/signin"),
            json={"email": "john.doe@openwebui.com", "password": "password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@openwebui.com"
        assert data["role"] == "user"
        assert data["profile_image_url"] == "/user.png"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_guest_session(self):
        response = self.fast_api_client.post(self.create_url("/guest"))

        assert response.status_code == 403

        from open_webui.routers import auths as auths_router

        self.fast_api_client.app.state.config.ENABLE_GUEST_ACCESS = True
        response = self.fast_api_client.post(self.create_url("/guest"))

        assert response.status_code == 200
        data = response.json()
        assert data["guest"] is True
        assert data["role"] == "user"
        assert data["email"].startswith("guest-")
        assert data["email"].endswith("@guest.local")
        assert data["token"]
        assert response.cookies.get("token")

        guest_user = auths_router.Users.get_user_by_email(data["email"])
        assert guest_user is not None
        assert guest_user.role == "user"

    def test_guest_session_coerces_pending_or_admin_defaults_to_non_admin_user(self):
        self.fast_api_client.app.state.config.ENABLE_GUEST_ACCESS = True
        self.fast_api_client.app.state.config.DEFAULT_USER_ROLE = "pending"

        response = self.fast_api_client.post(self.create_url("/guest"))

        assert response.status_code == 200
        assert response.json()["role"] == "user"

        self.fast_api_client.app.state.config.DEFAULT_USER_ROLE = "admin"
        response = self.fast_api_client.post(self.create_url("/guest"))

        assert response.status_code == 200
        assert response.json()["role"] == "user"

    def test_signout_clears_guest_session_cookie(self):
        self.fast_api_client.app.state.config.ENABLE_GUEST_ACCESS = True
        guest_response = self.fast_api_client.post(self.create_url("/guest"))

        assert guest_response.status_code == 200
        assert guest_response.cookies.get("token")

        signout_response = self.fast_api_client.get(self.create_url("/signout"))

        assert signout_response.status_code == 200
        set_cookie = signout_response.headers.get("set-cookie", "")
        assert "token=" in set_cookie
        assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()

    def test_signin_without_auth_bootstraps_admin_without_fixed_password(self, monkeypatch):
        from open_webui.models.auths import Auth, get_db
        from open_webui.routers import auths as auths_router

        monkeypatch.setattr(auths_router, "WEBUI_AUTH", False)

        response = self.fast_api_client.post(
            self.create_url("/signin"),
            json={"email": "", "password": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@localhost"
        assert data["role"] == "admin"

        with get_db() as db:
            auth = db.query(Auth).filter_by(email="admin@localhost").first()

        assert auth is not None
        assert auth.password != "admin"

    def test_signin_without_auth_uses_existing_first_user(self, monkeypatch):
        from open_webui.routers import auths as auths_router
        from open_webui.utils.auth import get_password_hash

        monkeypatch.setattr(auths_router, "WEBUI_AUTH", False)

        user = self.auths.insert_new_auth(
            email="owner@example.com",
            password=get_password_hash("super-secret"),
            name="Owner",
            profile_image_url="/user.png",
            role="admin",
        )

        response = self.fast_api_client.post(
            self.create_url("/signin"),
            json={"email": "", "password": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == "owner@example.com"
        assert data["role"] == "admin"

    def test_signup(self):
        response = self.fast_api_client.post(
            self.create_url("/signup"),
            json={
                "name": "John Doe",
                "email": "john.doe@openwebui.com",
                "password": "password",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None and len(data["id"]) > 0
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@openwebui.com"
        assert data["role"] in ["admin", "user", "pending"]
        assert data["profile_image_url"] == "/user.png"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_add_user(self):
        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/add"),
                json={
                    "name": "John Doe 2",
                    "email": "john.doe2@openwebui.com",
                    "password": "password2",
                    "role": "admin",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None and len(data["id"]) > 0
        assert data["name"] == "John Doe 2"
        assert data["email"] == "john.doe2@openwebui.com"
        assert data["role"] == "admin"
        assert data["profile_image_url"] == "/user.png"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_get_admin_details(self):
        self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url("/admin/details"))

        assert response.status_code == 200
        assert response.json() == {
            "name": "John Doe",
            "email": "john.doe@openwebui.com",
        }

    def test_get_and_update_admin_config_includes_guest_access(self):
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url("/admin/config"))

        assert response.status_code == 200
        assert "ENABLE_GUEST_ACCESS" in response.json()

        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/admin/config"),
                json={
                    "SHOW_ADMIN_DETAILS": True,
                    "WEBUI_URL": "http://localhost:3000",
                    "ENABLE_SIGNUP": True,
                    "ENABLE_GUEST_ACCESS": True,
                    "ENABLE_API_KEY": True,
                    "ENABLE_API_KEY_ENDPOINT_RESTRICTIONS": False,
                    "API_KEY_ALLOWED_ENDPOINTS": "",
                    "DEFAULT_USER_ROLE": "user",
                    "JWT_EXPIRES_IN": "-1",
                    "ENABLE_COMMUNITY_SHARING": True,
                    "ENABLE_CHANNELS": False,
                    "ENABLE_USER_WEBHOOKS": True,
                },
            )

        assert response.status_code == 200
        assert response.json()["ENABLE_GUEST_ACCESS"] is True

    def test_create_api_key_(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(self.create_url("/api_key"))
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] is not None
        assert len(data["api_key"]) > 0

    def test_delete_api_key(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        self.users.update_user_api_key_by_id(user.id, "abc")
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.delete(self.create_url("/api_key"))
        assert response.status_code == 200
        assert response.json() == True
        db_user = self.users.get_user_by_id(user.id)
        assert db_user.api_key is None

    def test_get_api_key(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        self.users.update_user_api_key_by_id(user.id, "abc")
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.get(self.create_url("/api_key"))
        assert response.status_code == 200
        assert response.json() == {"api_key": "abc"}
