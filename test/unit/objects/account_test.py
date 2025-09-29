from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import AccountSettingsInterfacesForNewLinodes
from linode_api4.objects import (
    Account,
    AccountAvailability,
    AccountBetaProgram,
    AccountSettings,
    Database,
    Domain,
    Event,
    Firewall,
    Image,
    Instance,
    Invoice,
    Login,
    LongviewClient,
    NodeBalancer,
    OAuthClient,
    PaymentMethod,
    ServiceTransfer,
    StackScript,
    User,
    UserGrants,
    Volume,
    get_obj_grants,
)
from linode_api4.objects.account import ChildAccount
from linode_api4.objects.vpc import VPC


class InvoiceTest(ClientBaseCase):
    """
    Tests methods of the Invoice
    """

    def test_get_invoice(self):
        """
        Tests that an invoice is loaded correctly by ID
        """
        invoice = Invoice(self.client, 123456)
        self.assertEqual(invoice._populated, False)

        self.assertEqual(invoice.label, "Invoice #123456")
        self.assertEqual(invoice._populated, True)

        self.assertEqual(invoice.date, datetime(2015, 1, 1, 5, 1, 2))
        self.assertEqual(invoice.total, 9.51)

    def test_get_invoice_items(self):
        """
        Tests that you can get items for an invoice
        """
        invoice = Invoice(self.client, 123456)
        items = invoice.items

        self.assertEqual(len(items), 1)
        item = items[0]

        self.assertEqual(item.label, "Linode 2048 - Example")
        self.assertEqual(item.type, "hourly")
        self.assertEqual(item.amount, 9.51)
        self.assertEqual(item.quantity, 317)
        self.assertEqual(item.unit_price, "0.03")
        self.assertEqual(
            item.from_date,
            datetime(year=2014, month=12, day=19, hour=0, minute=27, second=2),
        )
        self.assertEqual(
            item.to_date,
            datetime(year=2015, month=1, day=1, hour=4, minute=59, second=59),
        )

    def test_get_account(self):
        """
        Tests that an account is loaded correctly by email
        """
        account = Account(self.client, "support@linode.com", {})

        self.assertEqual(account.email, "support@linode.com")
        self.assertEqual(account.state, "PA")
        self.assertEqual(account.city, "Philadelphia")
        self.assertEqual(account.phone, "123-456-7890")
        self.assertEqual(account.tax_id, "")
        self.assertEqual(account.balance, 0)
        self.assertEqual(account.company, "Linode")
        self.assertEqual(account.address_1, "3rd & Arch St")
        self.assertEqual(account.address_2, "")
        self.assertEqual(account.zip, "19106")
        self.assertEqual(account.first_name, "Test")
        self.assertEqual(account.last_name, "Guy")
        self.assertEqual(account.country, "US")
        self.assertIsNotNone(account.capabilities)
        self.assertIsNotNone(account.active_promotions)
        self.assertEqual(account.balance_uninvoiced, 145)
        self.assertEqual(account.billing_source, "akamai")
        self.assertEqual(account.euuid, "E1AF5EEC-526F-487D-B317EBEB34C87D71")
        self.assertIn("Linode Interfaces", account.capabilities)

    def test_get_login(self):
        """
        Tests that a login is loaded correctly by ID
        """
        login = Login(self.client, 123)

        self.assertEqual(login.id, 123)
        self.assertEqual(login.ip, "192.0.2.0")
        self.assertEqual(login.restricted, True)
        self.assertEqual(login.status, "successful")
        self.assertEqual(login.username, "test-user")

    def test_get_account_settings(self):
        """
        Tests that account settings are loaded correctly
        """
        settings = AccountSettings(self.client, False, {})

        self.assertEqual(settings.longview_subscription.id, "longview-100")
        self.assertEqual(settings.managed, False)
        self.assertEqual(settings.network_helper, False)
        self.assertEqual(settings.object_storage, "active")
        self.assertEqual(settings.backups_enabled, True)
        self.assertEqual(
            settings.interfaces_for_new_linodes,
            AccountSettingsInterfacesForNewLinodes.linode_default_but_legacy_config_allowed,
        )

    def test_post_account_settings(self):
        """
        Tests that account settings can be updated successfully
        """
        settings = self.client.account.settings()

        settings.network_helper = True
        settings.backups_enabled = False
        settings.interfaces_for_new_linodes = (
            AccountSettingsInterfacesForNewLinodes.linode_only
        )

        with self.mock_put("/account/settings") as m:
            settings.save()

            assert m.call_data == {
                "network_helper": True,
                "backups_enabled": False,
                "interfaces_for_new_linodes": AccountSettingsInterfacesForNewLinodes.linode_only,
                "maintenance_policy": "linode/migrate",
            }

    def test_update_account_settings(self):
        """
        Tests that account settings can be updated
        """
        with self.mock_put("account/settings") as m:
            settings = AccountSettings(self.client, False, {})

            settings.maintenance_policy = "linode/migrate"
            settings.save()

            self.assertEqual(m.call_url, "/account/settings")
            self.assertEqual(
                m.call_data,
                {
                    "maintenance_policy": "linode/migrate",
                },
            )

    def test_get_event(self):
        """
        Tests that an event is loaded correctly by ID
        """
        event = Event(self.client, 123, {})

        self.assertEqual(event.action, "ticket_create")
        self.assertEqual(event.created, datetime(2025, 3, 25, 12, 0, 0))
        self.assertEqual(event.duration, 300.56)

        self.assertIsNotNone(event.entity)
        self.assertEqual(event.entity.id, 11111)
        self.assertEqual(event.entity.label, "Problem booting my Linode")
        self.assertEqual(event.entity.type, "ticket")
        self.assertEqual(event.entity.url, "/v4/support/tickets/11111")

        self.assertEqual(event.id, 123)
        self.assertEqual(event.message, "Ticket created for user issue.")
        self.assertIsNone(event.percent_complete)
        self.assertIsNone(event.rate)
        self.assertTrue(event.read)

        self.assertIsNotNone(event.secondary_entity)
        self.assertEqual(event.secondary_entity.id, "linode/debian9")
        self.assertEqual(event.secondary_entity.label, "linode1234")
        self.assertEqual(event.secondary_entity.type, "linode")
        self.assertEqual(
            event.secondary_entity.url, "/v4/linode/instances/1234"
        )

        self.assertTrue(event.seen)
        self.assertEqual(event.status, "completed")
        self.assertEqual(event.username, "exampleUser")

        self.assertEqual(event.maintenance_policy_set, "Tentative")
        self.assertEqual(event.description, "Scheduled maintenance")
        self.assertEqual(event.source, "user")
        self.assertEqual(event.not_before, datetime(2025, 3, 25, 12, 0, 0))
        self.assertEqual(event.start_time, datetime(2025, 3, 25, 12, 30, 0))
        self.assertEqual(event.complete_time, datetime(2025, 3, 25, 13, 0, 0))

    def test_get_invoice(self):
        """
        Tests that an invoice is loaded correctly by ID
        """
        invoice = Invoice(self.client, 123, {})

        self.assertEqual(invoice.date, datetime(2018, 1, 1, 0, 1, 1))
        self.assertEqual(invoice.id, 123)
        self.assertEqual(invoice.label, "Invoice")
        self.assertEqual(invoice.subtotal, 120.25)
        self.assertEqual(invoice.tax, 12.25)
        self.assertEqual(invoice.total, 132.5)
        self.assertIsNotNone(invoice.tax_summary)

    def test_get_oauth_client(self):
        """
        Tests that an oauth client is loaded correctly by ID
        """
        client = OAuthClient(self.client, "2737bf16b39ab5d7b4a1", {})

        self.assertEqual(client.id, "2737bf16b39ab5d7b4a1")
        self.assertEqual(client.label, "Test_Client_1")
        self.assertFalse(client.public)
        self.assertEqual(
            client.redirect_uri, "https://example.org/oauth/callback"
        )
        self.assertEqual(client.secret, "<REDACTED>")
        self.assertEqual(client.status, "active")
        self.assertEqual(
            client.thumbnail_url,
            "https://api.linode.com/v4/account/clients/2737bf16b39ab5d7b4a1/thumbnail",
        )

    def test_get_user(self):
        """
        Tests that a user is loaded correctly by username
        """
        user = User(self.client, "test-user", {})

        self.assertEqual(user.username, "test-user")
        self.assertEqual(user.email, "test-user@linode.com")
        self.assertTrue(user.restricted)
        self.assertTrue(user.tfa_enabled)
        self.assertIsNotNone(user.ssh_keys)

    def test_get_service_transfer(self):
        """
        Tests that a service transfer is loaded correctly by token
        """
        serviceTransfer = ServiceTransfer(self.client, "12345")

        self.assertEqual(serviceTransfer.token, "12345")
        self.assertTrue(serviceTransfer.is_sender)
        self.assertEqual(serviceTransfer.status, "pending")

    def test_get_payment_method(self):
        """
        Tests that a payment method is loaded correctly by ID
        """
        paymentMethod = PaymentMethod(self.client, 123)

        self.assertEqual(paymentMethod.id, 123)
        self.assertTrue(paymentMethod.is_default)
        self.assertEqual(paymentMethod.type, "credit_card")

    def test_payment_method_make_default(self):
        """
        Tests that making a payment method default creates the correct api request.
        """
        paymentMethod = PaymentMethod(self.client, 123)

        with self.mock_post({}) as m:
            paymentMethod.payment_method_make_default()
            self.assertEqual(
                m.call_url, "/account/payment-methods/123/make-default"
            )

    def test_service_transfer_accept(self):
        """
        Tests that accepting a service transfer creates the correct api request.
        """
        serviceTransfer = ServiceTransfer(self.client, "12345")

        with self.mock_post({}) as m:
            serviceTransfer.service_transfer_accept()
            self.assertEqual(
                m.call_url, "/account/service-transfers/12345/accept"
            )


class AccountBetaProgramTest(ClientBaseCase):
    """
    Tests methods of the AccountBetaProgram
    """

    def test_account_beta_program_api_get(self):
        beta_id = "cool"
        account_beta_url = "/account/betas/{}".format(beta_id)

        with self.mock_get(account_beta_url) as m:
            beta = AccountBetaProgram(self.client, beta_id)
            self.assertEqual(beta.id, beta_id)
            self.assertEqual(beta.enrolled, datetime(2018, 1, 2, 3, 4, 5))
            self.assertEqual(beta.started, datetime(2018, 1, 2, 3, 4, 5))
            self.assertEqual(beta.ended, datetime(2018, 1, 2, 3, 4, 5))

            self.assertEqual(m.call_url, account_beta_url)


class AccountAvailabilityTest(ClientBaseCase):
    """
    Test methods of the AccountAvailability
    """

    def test_account_availability_api_list(self):
        with self.mock_get("/account/availability") as m:
            availabilities = self.client.account.availabilities()

            for avail in availabilities:
                assert avail.region is not None
                assert len(avail.unavailable) == 0
                assert len(avail.available) > 0

                self.assertEqual(m.call_url, "/account/availability")

    def test_account_availability_api_get(self):
        region_id = "us-east"
        account_availability_url = "/account/availability/{}".format(region_id)

        with self.mock_get(account_availability_url) as m:
            availability = AccountAvailability(self.client, region_id)
            self.assertEqual(availability.region, region_id)
            self.assertEqual(availability.unavailable, [])
            self.assertEqual(availability.available, ["Linodes", "Kubernetes"])

            self.assertEqual(m.call_url, account_availability_url)


class ChildAccountTest(ClientBaseCase):
    """
    Test methods of the ChildAccount
    """

    def test_child_account_api_list(self):
        result = self.client.account.child_accounts()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].euuid, "E1AF5EEC-526F-487D-B317EBEB34C87D71")

    def test_child_account_create_token(self):
        child_account = self.client.load(ChildAccount, 123456)
        with self.mock_post("/account/child-accounts/123456/token") as m:
            token = child_account.create_token()
            self.assertEqual(token.token, "abcdefghijklmnop")
            self.assertEqual(m.call_data, {})


def test_get_user_grant():
    """
    Tests that a user grant is loaded correctly
    """
    grants = get_obj_grants()

    assert grants.count(("linode", Instance)) > 0
    assert grants.count(("domain", Domain)) > 0
    assert grants.count(("stackscript", StackScript)) > 0
    assert grants.count(("nodebalancer", NodeBalancer)) > 0
    assert grants.count(("volume", Volume)) > 0
    assert grants.count(("image", Image)) > 0
    assert grants.count(("longview", LongviewClient)) > 0
    assert grants.count(("database", Database)) > 0
    assert grants.count(("firewall", Firewall)) > 0
    assert grants.count(("vpc", VPC)) > 0


def test_user_grants_serialization():
    """
    Tests that user grants from JSON is serialized correctly
    """
    user_grants_json = {
        "database": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "domain": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "firewall": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "global": {
            "account_access": "read_only",
            "add_databases": True,
            "add_domains": True,
            "add_firewalls": True,
            "add_images": True,
            "add_linodes": True,
            "add_longview": True,
            "add_nodebalancers": True,
            "add_stackscripts": True,
            "add_volumes": True,
            "add_vpcs": True,
            "cancel_account": False,
            "child_account_access": True,
            "longview_subscription": True,
        },
        "image": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "linode": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "longview": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "nodebalancer": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "stackscript": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "volume": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
        "vpc": [
            {"id": 123, "label": "example-entity", "permissions": "read_only"}
        ],
    }

    expected_serialized_grants = deepcopy(user_grants_json)

    for grants in expected_serialized_grants.values():
        if isinstance(grants, Iterable):
            for grant in grants:
                if isinstance(grant, dict) and "label" in grant:
                    del grant["label"]

    assert (
        UserGrants(None, None, user_grants_json)._serialize()
        == expected_serialized_grants
    )
