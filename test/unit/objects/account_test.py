from datetime import datetime
from test.unit.base import ClientBaseCase

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
    Volume,
    get_obj_grants,
)


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

    def test_get_event(self):
        """
        Tests that an event is loaded correctly by ID
        """
        event = Event(self.client, 123, {})

        self.assertEqual(event.action, "ticket_create")
        self.assertEqual(event.created, datetime(2018, 1, 1, 0, 1, 1))
        self.assertEqual(event.duration, 300.56)
        self.assertIsNotNone(event.entity)
        self.assertEqual(event.id, 123)
        self.assertEqual(event.message, "None")
        self.assertIsNone(event.percent_complete)
        self.assertIsNone(event.rate)
        self.assertTrue(event.read)
        self.assertIsNotNone(event.secondary_entity)
        self.assertTrue(event.seen)
        self.assertIsNone(event.status)
        self.assertIsNone(event.time_remaining)
        self.assertEqual(event.username, "exampleUser")

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

    def test_get_user_grant(self):
        """
        Tests that a user grant is loaded correctly
        """
        grants = get_obj_grants()

        self.assertTrue(grants.count(("linode", Instance)) > 0)
        self.assertTrue(grants.count(("domain", Domain)) > 0)
        self.assertTrue(grants.count(("stackscript", StackScript)) > 0)
        self.assertTrue(grants.count(("nodebalancer", NodeBalancer)) > 0)
        self.assertTrue(grants.count(("volume", Volume)) > 0)
        self.assertTrue(grants.count(("image", Image)) > 0)
        self.assertTrue(grants.count(("longview", LongviewClient)) > 0)
        self.assertTrue(grants.count(("database", Database)) > 0)
        self.assertTrue(grants.count(("firewall", Firewall)) > 0)

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

    def test_account_availability_api_get(self):
        region_id = "us-east"
        account_availability_url = "/account/availability/{}".format(region_id)

        with self.mock_get(account_availability_url) as m:
            availability = AccountAvailability(self.client, region_id)
            self.assertEqual(availability.region, region_id)
            self.assertEqual(availability.unavailable, [])

            self.assertEqual(m.call_url, account_availability_url)
