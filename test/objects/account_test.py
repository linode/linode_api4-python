from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import (
    Account,
    AccountSettings,
    Database,
    Domain,
    Event,
    Image,
    Instance,
    Invoice,
    LongviewClient,
    NodeBalancer,
    OAuthClient,
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

    def test_get_account_settings(self):
        settings = AccountSettings(self.client, False, {})

        self.assertEqual(settings.longview_subscription.id, "longview-100")
        self.assertEqual(settings.managed, False)
        self.assertEqual(settings.network_helper, False)
        self.assertEqual(settings.object_storage, "active")
        self.assertEqual(settings.backups_enabled, True)

    def test_get_event(self):
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
        invoice = Invoice(self.client, 123, {})

        self.assertEqual(invoice.date, datetime(2018, 1, 1, 0, 1, 1))
        self.assertEqual(invoice.id, 123)
        self.assertEqual(invoice.label, "Invoice")
        self.assertEqual(invoice.subtotal, 120.25)
        self.assertEqual(invoice.tax, 12.25)
        self.assertEqual(invoice.total, 132.5)
        self.assertIsNotNone(invoice.tax_summary)

    def test_get_oauth_client(self):
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
        user = User(self.client, "test-user", {})

        self.assertEqual(user.username, "test-user")
        self.assertEqual(user.email, "test-user@linode.com")
        self.assertTrue(user.restricted)
        self.assertTrue(user.tfa_enabled)
        self.assertIsNotNone(user.ssh_keys)

    def test_get_user_grant(self):
        grants = get_obj_grants()

        self.assertTrue(grants.count(("linode", Instance)) > 0)
        self.assertTrue(grants.count(("domain", Domain)) > 0)
        self.assertTrue(grants.count(("stackscript", StackScript)) > 0)
        self.assertTrue(grants.count(("nodebalancer", NodeBalancer)) > 0)
        self.assertTrue(grants.count(("volume", Volume)) > 0)
        self.assertTrue(grants.count(("image", Image)) > 0)
        self.assertTrue(grants.count(("longview", LongviewClient)) > 0)
        self.assertTrue(grants.count(("database", Database)) > 0)

    def test_event_seen(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post({}) as m:
            account.event_seen(123)
            self.assertEqual(m.call_url, "/account/events/123/seen")

    def test_list_logins(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/logins") as m:
            result = account.list_logins()
            self.assertEqual(m.call_url, "/account/logins")
            self.assertEqual(len(result), 1)

    def test_view_login(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/logins/123") as m:
            result = account.view_login(123)
            self.assertEqual(m.call_url, "/account/logins/123")
            self.assertEqual(result["id"], 123)
            self.assertEqual(result["ip"], "192.0.2.0")
            self.assertTrue(result["restricted"])
            self.assertEqual(result["status"], "successful")
            self.assertEqual(result["username"], "test-user")

    def test_maintenance_list(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/maintenance") as m:
            result = account.maintenance_list()
            self.assertEqual(m.call_url, "/account/maintenance")
            self.assertEqual(len(result), 1)

    def test_notification_list(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/notifications") as m:
            result = account.notification_list()
            self.assertEqual(m.call_url, "/account/notifications")
            self.assertEqual(len(result), 1)

    def test_payment_methods_list(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/payment-methods") as m:
            result = account.payment_methods_list()
            self.assertEqual(m.call_url, "/account/payment-methods")
            self.assertEqual(len(result), 1)

    def test_add_payment_method(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post({}) as m:
            account.add_payment_method({"data": {"card_number": "123456789100", "expiry_month": 1, "expiry_year": 2028, "cvv": 111}}, True, "credit_card")
            self.assertEqual(m.call_url, "/account/payment-methods")
            self.assertEqual(m.call_data["type"], "credit_card")
            self.assertTrue(m.call_data["is_default"])
            self.assertIsNotNone(m.call_data["data"])

    def test_payment_method_view(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/payment-methods/123") as m:
            result = account.payment_method_view(123)
            self.assertEqual(m.call_url, "/account/payment-methods/123")
            self.assertEqual(result["id"], 123)
            self.assertIsNotNone(result["data"])
            self.assertTrue(result["is_default"])
            self.assertEqual(result["type"], "credit_card")

    def test_payment_method_make_default(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post({}) as m:
            account.payment_method_make_default(123)
            self.assertEqual(m.call_url, "/account/payment-methods/123/make-default")

    def test_add_promo_code(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post("/account/promo-codes") as m:
            account.add_promo_code("123promo456")
            self.assertEqual(m.call_url, "/account/promo-codes")
            self.assertEqual(m.call_data["promo_code"], "123promo456")

    def test_service_transfers_list(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/service-transfers") as m:
            result = account.service_transfers_list()
            self.assertEqual(m.call_url, "/account/service-transfers")
            self.assertEqual(len(result), 1)

    def test_service_transfer_create(self):
        account = Account(self.client, "support@linode.com", {})

        data = {"entities": {"linodes": [111,222]}}
        response = {
                        "created": "2021-02-11T16:37:03",
                        "entities": {
                            "linodes": [
                            111,
                            222
                            ]
                        },
                        "expiry": "2021-02-12T16:37:03",
                        "is_sender": True,
                        "status": "pending",
                        "token": "123E4567-E89B-12D3-A456-426614174000",
                        "updated": "2021-02-11T16:37:03"
                    }

        with self.mock_post(response) as m:
            account.service_transfer_create(data)
            self.assertEqual(m.call_url, "/account/service-transfers")

    def test_service_transfer_view(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_get("/account/service-transfers/12345") as m:
            result = account.service_transfer_view(12345)
            self.assertEqual(m.call_url, "/account/service-transfers/12345")
            self.assertEqual(m.call_data["token"], 12345)
            self.assertEqual(result["token"], "12345")
            self.assertEqual(result["status"], "pending")
            self.assertTrue(result["is_sender"])
            self.assertIsNotNone(result["entities"])

    def test_service_transfer_accept(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post({}) as m:
            account.service_transfer_accept(123)
            self.assertEqual(m.call_url, "/account/service-transfers/123/accept")

    def test_linode_managed_enable(self):
        account = Account(self.client, "support@linode.com", {})

        with self.mock_post({}) as m:
            account.linode_managed_enable()
            self.assertEqual(m.call_url, "/account/settings/managed-enable")
