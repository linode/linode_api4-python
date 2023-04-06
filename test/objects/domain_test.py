from linode_api4.objects import Domain
from test.base import ClientBaseCase

class DomainGeneralTest(ClientBaseCase):
    """
    Tests methods of the Domain class.
    """

    def test_reproduce_error(self):

        # domain = Domain(self.client, 12345)

        # self.assertEqual(domain.domain, "example.org")
        # self.assertEqual(domain.type, "master")

        # params = {
        #     "type": "slave",
        #     "master_ips": ["127.0.0.1"]
        # }

        with self.mock_put('domains/12345') as m:
            domain = self.client.load(Domain, 12345)

            domain.type = "slave"
            domain.master_ips = ["127.0.0.1"]
            domain.save()

        #result = domain._client.put(Domain.api_endpoint, model=domain, data=params)