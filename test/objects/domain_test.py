from linode_api4.objects import Domain
from test.base import ClientBaseCase

class DomainGeneralTest(ClientBaseCase):
    """
    Tests methods of the Domain class.
    """

    def test_save_null_values_excluded(self):
        with self.mock_put('domains/12345') as m:
            domain = self.client.load(Domain, 12345)

            domain.type = "slave"
            domain.master_ips = ["127.0.0.1"]
            domain.save()

            self.assertTrue('group' not in m.call_data.keys())