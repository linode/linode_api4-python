from datetime import datetime

from test.base import ClientBaseCase

from linode_api4.objects import Invoice


class InvoiceTest(ClientBaseCase):
    """
    Tests methods of the Invoice
    """
    def test_get_invoice(self):
        invoice = Invoice(self.client, 123456)
        self.assertEqual(invoice._populated, False)

        self.assertEqual(invoice.label, 'Invoice #123456')
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
        self.assertEqual(item.from_date, datetime(year=2014, month=12, day=19, hour=0, minute=27, second=2))
        self.assertEqual(item.to_date, datetime(year=2015, month=1, day=1, hour=4, minute=59, second=59))
