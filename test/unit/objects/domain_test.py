from test.unit.base import ClientBaseCase

from linode_api4.objects import Domain, DomainRecord


class DomainGeneralTest(ClientBaseCase):
    """
    Tests methods of the Domain class.
    """

    def test_domain_get(self):
        domain_record = DomainRecord(self.client, 123456, 12345)

        self.assertEqual(domain_record.id, 123456)

    def test_save_null_values_excluded(self):
        with self.mock_put("domains/12345") as m:
            domain = self.client.load(Domain, 12345)

            domain.type = "slave"
            domain.master_ips = ["127.0.0.1"]
            domain.save()
            self.assertTrue("group" not in m.call_data.keys())

    def test_zone_file_view(self):
        domain = Domain(self.client, 12345)

        with self.mock_get("/domains/12345/zone-file") as m:
            result = domain.zone_file_view()
            self.assertEqual(m.call_url, "/domains/12345/zone-file")
            self.assertIsNotNone(result)

    def test_clone(self):
        domain = Domain(self.client, 12345)

        with self.mock_post("/domains/12345/clone") as m:
            clone = domain.clone("example.org")
            self.assertEqual(m.call_url, "/domains/12345/clone")
            self.assertEqual(m.call_data["domain"], "example.org")
            self.assertEqual(clone.id, 12345)

    def test_import(self):
        domain = Domain(self.client, 12345)

        with self.mock_post("/domains/import") as m:
            domain.domain_import("example.org", "examplenameserver.com")
            self.assertEqual(m.call_url, "/domains/import")
            self.assertEqual(m.call_data["domain"], "example.org")
            self.assertEqual(
                m.call_data["remote_nameserver"], "examplenameserver.com"
            )

        with self.mock_post("/domains/import") as m:
            domain.domain_import(domain, "examplenameserver.com")
            self.assertEqual(m.call_url, "/domains/import")
            self.assertEqual(m.call_data["domain"], "example.org")
            self.assertEqual(
                m.call_data["remote_nameserver"], "examplenameserver.com"
            )
