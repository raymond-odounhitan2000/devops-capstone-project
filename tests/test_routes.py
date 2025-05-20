"""
Account API Service Test Suite

Run tests with:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

# Constants
BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}

# Set default DB URI for testing
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}


######################################################################
#  T E S T   S U I T E
######################################################################
class TestAccountService(TestCase):
    """Test Suite for the Account Service"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False  # Disable HTTPS enforcement in test mode
        init_db(app)
        talisman.force_https = False

    def setUp(self):
        """Run before each test"""
        db.session.query(Account).delete()
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Run after each test"""
        db.session.remove()

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################
    def _create_accounts(self, count):
        """Factory method to create multiple test accounts"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            account.id = response.get_json()["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """GET / - It should return 200 OK"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_health(self):
        """GET /health - It should return 'OK'"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["status"], "OK")

    def test_create_account(self):
        """POST /accounts - It should create a new account"""
        account = AccountFactory()
        resp = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(data["phone_number"], account.phone_number)
        self.assertEqual(data["date_joined"], str(account.date_joined))
        self.assertIsNotNone(resp.headers.get("Location"))

    def test_bad_request(self):
        """POST /accounts - Should return 400 with invalid data"""
        resp = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """POST /accounts - Should return 415 with wrong media type"""
        account = AccountFactory()
        resp = self.client.post(
            BASE_URL, json=account.serialize(), content_type="text/html"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        """GET /accounts/{id} - It should return a single account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], account.name)

    def test_account_not_found(self):
        """GET /accounts/0 - Should return 404 if not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """GET /accounts - It should return a list of accounts"""
        self._create_accounts(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.get_json()), 5)

    def test_update_account(self):
        """PUT /accounts/{id} - It should update an existing account"""
        account = self._create_accounts(1)[0]
        updated_data = account.serialize()
        updated_data["name"] = "Updated Name"

        resp = self.client.put(f"{BASE_URL}/{account.id}", json=updated_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], "Updated Name")

    def test_delete_account(self):
        """DELETE /accounts/{id} - It should delete the account"""
        account = self._create_accounts(1)[0]

        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Ensure it's deleted
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        """DELETE /accounts - Should return 405 METHOD NOT ALLOWED"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
      
    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check for the CORS header
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
