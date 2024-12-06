"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_list_accounts(self):
        """It should list all Accounts"""
        account = {}
        response = {}
        for i in range(10):
            account[i] = AccountFactory()
            response[i] = self.client.post(
                BASE_URL,
                json=account[i].serialize(),
                content_type="application/json"
            )
            self.assertEqual(response[i].status_code, status.HTTP_201_CREATED)
        new_response = self.client.get(BASE_URL)
        self.assertEqual(new_response.status_code, status.HTTP_200_OK)
        new_accounts = new_response.get_json()

        # Check the data is correct
        for i in range(10): 
            self.assertEqual(new_accounts[i]["name"], account[i].name)
            self.assertEqual(new_accounts[i]["email"], account[i].email)
            self.assertEqual(new_accounts[i]["address"], account[i].address)
            self.assertEqual(new_accounts[i]["phone_number"], account[i].phone_number)
            self.assertEqual(new_accounts[i]["date_joined"], str(account[i].date_joined))


    def test_read_account(self):
        """It should read an Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_account = response.get_json()
        created_id = created_account["id"]
        READ_URL = "/accounts/{}".format(created_id)
        found_response = self.client.get(READ_URL)
        self.assertEqual(found_response.status_code, status.HTTP_200_OK)
        found_account = found_response.get_json()

        # Check the data is correct 
        self.assertEqual(found_account["id"], created_account["id"])
        self.assertEqual(found_account["name"], account.name)
        self.assertEqual(found_account["email"], account.email)
        self.assertEqual(found_account["address"], account.address)
        self.assertEqual(found_account["phone_number"], account.phone_number)
        self.assertEqual(found_account["date_joined"], str(account.date_joined))

    def test_read_notvalid_account(self):
        """It should read a non-existing Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_account = response.get_json()
        created_id = created_account["id"]
        non_valid_id = created_id + 100
        READ_URL = BASE_URL + f"/{non_valid_id}"
        not_found_response = self.client.get(READ_URL)
        self.assertEqual(not_found_response.status_code, status.HTTP_404_NOT_FOUND)
        