from test.unit.base import ClientBaseCase

from linode_api4.objects import SupportTicket


class SupportTest(ClientBaseCase):
    """
    Tests methods of the SupportTicket class
    """

    def test_get_support_ticket(self):
        ticket = SupportTicket(self.client, 123)

        self.assertIsNotNone(ticket.attachments)
        self.assertFalse(ticket.closable)
        self.assertIsNotNone(ticket.entity)
        self.assertEqual(ticket.gravatar_id, "474a1b7373ae0be4132649e69c36ce30")
        self.assertEqual(ticket.id, 123)
        self.assertEqual(ticket.opened_by, "some_user")
        self.assertEqual(ticket.status, "open")
        self.assertEqual(ticket.updated_by, "some_other_user")

    def test_support_ticket_close(self):
        ticket = SupportTicket(self.client, 123)

        with self.mock_post({}) as m:
            ticket.support_ticket_close()
            self.assertEqual(m.call_url, "/support/tickets/123/close")
