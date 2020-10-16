from datetime import datetime

from test.base import ClientBaseCase

from linode_api4 import LongviewSubscription


class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """
    def test_get_no_empty_body(self):
        """
        Tests that a valid JSON body is passed for a GET call
        """
        with self.mock_get('linode/instances') as m:
            self.client.regions()

            self.assertEqual(m.call_data_raw, None)


    def test_get_account(self):
        a = self.client.account()
        self.assertEqual(a._populated, True)

        self.assertEqual(a.first_name, 'Test')
        self.assertEqual(a.last_name, 'Guy')
        self.assertEqual(a.email, 'support@linode.com')
        self.assertEqual(a.phone, '123-456-7890')
        self.assertEqual(a.company, 'Linode')
        self.assertEqual(a.address_1, '3rd & Arch St')
        self.assertEqual(a.address_2, '')
        self.assertEqual(a.city, 'Philadelphia')
        self.assertEqual(a.state, 'PA')
        self.assertEqual(a.country, 'US')
        self.assertEqual(a.zip, '19106')
        self.assertEqual(a.tax_id, '')
        self.assertEqual(a.balance, 0)
        self.assertEqual(a.capabilities, ["Linodes","NodeBalancers","Block Storage","Object Storage"])

    def test_get_regions(self):
        r = self.client.regions()

        self.assertEqual(len(r), 11)
        for region in r:
            self.assertTrue(region._populated)
            self.assertIsNotNone(region.id)
            self.assertIsNotNone(region.country)
            if region.id in ('us-east', 'eu-central', 'ap-south'):
                self.assertEqual(region.capabilities, ["Linodes","NodeBalancers","Block Storage","Object Storage"])
            else:
                self.assertEqual(region.capabilities, ["Linodes","NodeBalancers","Block Storage"])
            self.assertEqual(region.status, "ok")
            self.assertIsNotNone(region.resolvers)
            self.assertIsNotNone(region.resolvers.ipv4)
            self.assertIsNotNone(region.resolvers.ipv6)

    def test_get_images(self):
        r = self.client.images()

        self.assertEqual(len(r), 4)
        for image in r:
            self.assertTrue(image._populated)
            self.assertIsNotNone(image.id)

    def test_get_domains(self):
        """
        Tests that domains can be retrieved and are marshalled properly
        """
        r = self.client.domains()

        self.assertEqual(len(r), 1)
        domain = r.first()

        self.assertEqual(domain.domain, 'example.org')
        self.assertEqual(domain.type, 'master')
        self.assertEqual(domain.id, 12345)
        self.assertEqual(domain.axfr_ips, [])
        self.assertEqual(domain.retry_sec, 0)
        self.assertEqual(domain.ttl_sec, 300)
        self.assertEqual(domain.status, 'active')
        self.assertEqual(domain.master_ips, [],)
        self.assertEqual(domain.description, "",)
        self.assertEqual(domain.group, "",)
        self.assertEqual(domain.expire_sec, 0,)
        self.assertEqual(domain.soa_email, "test@example.org",)
        self.assertEqual(domain.refresh_sec, 0)

    def test_image_create(self):
        """
        Tests that an Image can be created successfully
        """
        with self.mock_post('images/private/123') as m:
            i = self.client.image_create(654, 'Test-Image', 'This is a test')

            self.assertIsNotNone(i)
            self.assertEqual(i.id, 'private/123')

            self.assertEqual(m.call_url, '/images')

            self.assertEqual(m.call_data, {
                "disk_id": 654,
                "label": "Test-Image",
                "description": "This is a test",
            })

    def test_get_volumes(self):
        v = self.client.volumes()

        self.assertEqual(len(v), 2)
        self.assertEqual(v[0].label, 'block1')
        self.assertEqual(v[0].region.id, 'us-east-1a')
        self.assertEqual(v[1].label, 'block2')
        self.assertEqual(v[1].size, 100)

        assert v[0].tags == ["something"]
        assert v[1].tags == []

    def test_get_tags(self):
        """
        Tests that a list of Tags can be retrieved as expected
        """
        t = self.client.tags()

        self.assertEqual(len(t), 2)
        self.assertEqual(t[0].label, 'nothing')
        self.assertEqual(t[1].label, 'something')

    def test_tag_create(self):
        """
        Tests that creating a tag works as expected
        """
        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({'label':'nothing'}) as m:
            t = self.client.tag_create('nothing')

            self.assertIsNotNone(t)
            self.assertEqual(t.label, 'nothing')

            self.assertEqual(m.call_url, '/tags')
            self.assertEqual(m.call_data, {
                'label': 'nothing',
            })

    def test_tag_create_with_ids(self):
        """
        Tests that creating a tag with IDs sends the correct request
        """
        instance1, instance2 = self.client.linode.instances()[:2]
        domain1 = self.client.domains().first()
        nodebalancer1, nodebalancer2 = self.client.nodebalancers()[:2]
        volume1, volume2 = self.client.volumes()[:2]

        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({'label':'pytest'}) as m:
            t = self.client.tag_create('pytest',
                                       instances=[instance1.id, instance2],
                                       nodebalancers=[nodebalancer1.id, nodebalancer2],
                                       domains=[domain1.id],
                                       volumes=[volume1.id, volume2])

            self.assertIsNotNone(t)
            self.assertEqual(t.label, 'pytest')

            self.assertEqual(m.call_url, '/tags')
            self.assertEqual(m.call_data, {
                'label': 'pytest',
                'linodes': [instance1.id, instance2.id],
                'domains': [domain1.id],
                'nodebalancers': [nodebalancer1.id, nodebalancer2.id],
                'volumes': [volume1.id, volume2.id],
            })

    def test_tag_create_with_entities(self):
        """
        Tests that creating a tag with entities sends the correct request
        """
        instance1, instance2 = self.client.linode.instances()[:2]
        domain = self.client.domains().first()
        nodebalancer = self.client.nodebalancers().first()
        volume = self.client.volumes().first()

        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({'label':'pytest'}) as m:
            t = self.client.tag_create('pytest',
                                       entities=[instance1, domain, nodebalancer, volume, instance2])

            self.assertIsNotNone(t)
            self.assertEqual(t.label, 'pytest')

            self.assertEqual(m.call_url, '/tags')
            self.assertEqual(m.call_data, {
                'label': 'pytest',
                'linodes': [instance1.id, instance2.id],
                'domains': [domain.id],
                'nodebalancers': [nodebalancer.id],
                'volumes': [volume.id],
            })


class AccountGroupTest(ClientBaseCase):
    """
    Tests methods of the AccountGroup
    """
    def test_get_settings(self):
        """
        Tests that account settings can be retrieved.
        """
        s = self.client.account.settings()
        self.assertEqual(s._populated, True)

        self.assertEqual(s.network_helper, False)
        self.assertEqual(s.managed, False)
        self.assertEqual(type(s.longview_subscription), LongviewSubscription)
        self.assertEqual(s.longview_subscription.id, 'longview-100')
        self.assertEqual(s.object_storage, "active")

    def test_get_invoices(self):
        """
        Tests that invoices can be retrieved
        """
        i = self.client.account.invoices()

        self.assertEqual(len(i), 1)
        invoice = i[0]

        self.assertEqual(invoice.id, 123456)
        self.assertEqual(invoice.date, datetime(2015, 1, 1, 5, 1, 2))
        self.assertEqual(invoice.label, 'Invoice #123456')
        self.assertEqual(invoice.total, 9.51)


class LinodeGroupTest(ClientBaseCase):
    """
    Tests methods of the LinodeGroup
    """
    def test_instance_create(self):
        """
        Tests that a Linode Instance can be created successfully
        """
        with self.mock_post('linode/instances/123') as m:
            l = self.client.linode.instance_create('g5-standard-1', 'us-east-1a')

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, '/linode/instances')

            self.assertEqual(m.call_data, {
                "region": "us-east-1a",
                "type": "g5-standard-1"
            })

    def test_instance_create_with_image(self):
        """
        Tests that a Linode Instance can be created with an image, and a password generated
        """
        with self.mock_post('linode/instances/123') as m:
            l, pw = self.client.linode.instance_create(
                'g5-standard-1', 'us-east-1a', image='linode/debian9')

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, '/linode/instances')

            self.assertEqual(m.call_data, {
                "region": "us-east-1a",
                "type": "g5-standard-1",
                "image": "linode/debian9",
                "root_pass": pw,
            })


class LongviewGroupTest(ClientBaseCase):
    """
    Tests methods of the LongviewGroup
    """
    def test_get_clients(self):
        """
        Tests that a list of LongviewClients can be retrieved
        """
        r = self.client.longview.clients()

        self.assertEqual(len(r), 2)
        self.assertEqual(r[0].label, "test_client_1")
        self.assertEqual(r[0].id, 1234)
        self.assertEqual(r[1].label, "longview5678")
        self.assertEqual(r[1].id, 5678)

    def test_client_create(self):
        """
        Tests that creating a client calls the api correctly
        """
        with self.mock_post('longview/clients/5678') as m:
            client = self.client.longview.client_create()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, 'longview5678')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {})

    def test_client_create_with_label(self):
        """
        Tests that creating a client with a label calls the api correctly
        """
        with self.mock_post('longview/clients/1234') as m:
            client = self.client.longview.client_create(label='test_client_1')

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 1234)
            self.assertEqual(client.label, 'test_client_1')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {"label": "test_client_1"})

    def test_get_subscriptions(self):
        """
        Tests that Longview subscriptions can be retrieved
        """
        r = self.client.longview.subscriptions()

        self.assertEqual(len(r), 4)

        expected_results = (
            ("longview-10", "Longview Pro 10 pack"),
            ("longview-100", "Longview Pro 100 pack"),
            ("longview-3", "Longview Pro 3 pack"),
            ("longview-40", "Longview Pro 40 pack"),
        )

        for result, (expected_id, expected_label) in zip(r, expected_results):
            self.assertEqual(result.id, expected_id)
            self.assertEqual(result.label, expected_label)


class ProfileGroupTest(ClientBaseCase):
    """
    Tests methods of the ProfileGroup
    """
    def test_get_sshkeys(self):
        """
        Tests that a list of SSH Keys can be retrieved
        """
        r = self.client.profile.ssh_keys()

        self.assertEqual(len(r), 2)

        key1, key2 = r

        self.assertEqual(key1.label, 'Home Ubuntu PC')
        self.assertEqual(key1.created, datetime(year=2018, month=9, day=14, hour=13,
                                                minute=0, second=0))
        self.assertEqual(key1.id, 22)
        self.assertEqual(
            key1.ssh_key, "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDe9NlKepJsI/S98"
                          "ISBJmG+cpEARtM0T1Qa5uTOUB/vQFlHmfQW07ZfA++ybPses0vRCD"
                          "eWyYPIuXcV5yFrf8YAW/Am0+/60MivT3jFY0tDfcrlvjdJAf1NpWO"
                          "TVlzv0gpsHFO+XIZcfEj3V0K5+pOMw9QGVf6Qbg8qzHVDPFdYKu3i"
                          "muc9KHY8F/b4DN/Wh17k3xAJpspCZEFkn0bdaYafJj0tPs0k78JRo"
                          "F2buc3e3M6dlvHaoON1votmrri9lut65OIpglOgPwE3QU8toGyyoC"
                          "MGaT4R7kIRjXy3WSyTMAi0KTAdxRK+IlDVMXWoE5TdLovd0a9L7qy"
                          "nZungKhKZUgFma7r9aTFVHXKh29Tzb42neDTpQnZ/Et735sDC1vfz"
                          "/YfgZNdgMUXFJ3+uA4M/36/Vy3Dpj2Larq3qY47RDFitmwSzwUlfz"
                          "tUoyiQ7e1WvXHT4N4Z8K2FPlTvNMg5CSjXHdlzcfiRFPwPn13w36v"
                          "TvAUxPvTa84P1eOLDp/JzykFbhHNh8Cb02yrU28zDeoTTyjwQs0eH"
                          "d1wtgIXJ8wuUgcaE4LgcgLYWwiKTq4/FnX/9lfvuAiPFl6KLnh23b"
                          "cKwnNA7YCWlb1NNLb2y+mCe91D8r88FGvbnhnOuVjd/SxQWDHtxCI"
                          "CmhW7erNJNVxYjtzseGpBLmRRUTsT038w== dorthu@dorthu-command")

    def test_client_create(self):
        """
        Tests that creating a client calls the api correctly
        """
        with self.mock_post('longview/clients/5678') as m:
            client = self.client.longview.client_create()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, 'longview5678')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {})

    def test_ssh_key_create(self):
        """
        Tests that creating an ssh key works as expected
        """
        with self.mock_post('profile/sshkeys/72') as m:
            key = self.client.profile.ssh_key_upload(
                         "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDe9NlKepJsI/S98"
                         "ISBJmG+cpEARtM0T1Qa5uTOUB/vQFlHmfQW07ZfA++ybPses0vRCD"
                         "eWyYPIuXcV5yFrf8YAW/Am0+/60MivT3jFY0tDfcrlvjdJAf1NpWO"
                         "TVlzv0gpsHFO+XIZcfEj3V0K5+pOMw9QGVf6Qbg8qzHVDPFdYKu3i"
                         "muc9KHY8F/b4DN/Wh17k3xAJpspCZEFkn0bdaYafJj0tPs0k78JRo"
                         "F2buc3e3M6dlvHaoON1votmrri9lut65OIpglOgPwE3QU8toGyyoC"
                         "MGaT4R7kIRjXy3WSyTMAi0KTAdxRK+IlDVMXWoE5TdLovd0a9L7qy"
                         "nZungKhKZUgFma7r9aTFVHXKh29Tzb42neDTpQnZ/Et735sDC1vfz"
                         "/YfgZNdgMUXFJ3+uA4M/36/Vy3Dpj2Larq3qY47RDFitmwSzwUlfz"
                         "tUoyiQ7e1WvXHT4N4Z8K2FPlTvNMg5CSjXHdlzcfiRFPwPn13w36v"
                         "TvAUxPvTa84P1eOLDp/JzykFbhHNh8Cb02yrU28zDeoTTyjwQs0eH"
                         "d1wtgIXJ8wuUgcaE4LgcgLYWwiKTq4/FnX/9lfvuAiPFl6KLnh23b"
                         "cKwnNA7YCWlb1NNLb2y+mCe91D8r88FGvbnhnOuVjd/SxQWDHtxCI"
                         "CmhW7erNJNVxYjtzseGpBLmRRUTsT038w==dorthu@dorthu-command",
                         'Work Laptop')

            self.assertIsNotNone(key)
            self.assertEqual(key.id, 72)
            self.assertEqual(key.label, 'Work Laptop')

            self.assertEqual(m.call_url, '/profile/sshkeys')
            self.assertEqual(m.call_data, {
                "ssh_key":  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDe9NlKepJsI/S98"
                            "ISBJmG+cpEARtM0T1Qa5uTOUB/vQFlHmfQW07ZfA++ybPses0vRCD"
                            "eWyYPIuXcV5yFrf8YAW/Am0+/60MivT3jFY0tDfcrlvjdJAf1NpWO"
                            "TVlzv0gpsHFO+XIZcfEj3V0K5+pOMw9QGVf6Qbg8qzHVDPFdYKu3i"
                            "muc9KHY8F/b4DN/Wh17k3xAJpspCZEFkn0bdaYafJj0tPs0k78JRo"
                            "F2buc3e3M6dlvHaoON1votmrri9lut65OIpglOgPwE3QU8toGyyoC"
                            "MGaT4R7kIRjXy3WSyTMAi0KTAdxRK+IlDVMXWoE5TdLovd0a9L7qy"
                            "nZungKhKZUgFma7r9aTFVHXKh29Tzb42neDTpQnZ/Et735sDC1vfz"
                            "/YfgZNdgMUXFJ3+uA4M/36/Vy3Dpj2Larq3qY47RDFitmwSzwUlfz"
                            "tUoyiQ7e1WvXHT4N4Z8K2FPlTvNMg5CSjXHdlzcfiRFPwPn13w36v"
                            "TvAUxPvTa84P1eOLDp/JzykFbhHNh8Cb02yrU28zDeoTTyjwQs0eH"
                            "d1wtgIXJ8wuUgcaE4LgcgLYWwiKTq4/FnX/9lfvuAiPFl6KLnh23b"
                            "cKwnNA7YCWlb1NNLb2y+mCe91D8r88FGvbnhnOuVjd/SxQWDHtxCI"
                            "CmhW7erNJNVxYjtzseGpBLmRRUTsT038w==dorthu@dorthu-command",
                "label": "Work Laptop"
            })

class ObjectStorageGroupTest(ClientBaseCase):
    """
    Tests for the ObjectStorageGroup
    """
    def test_get_clusters(self):
        """
        Tests that Object Storage Clusters can be retrieved
        """
        clusters = self.client.object_storage.clusters()

        self.assertEqual(len(clusters), 1)
        cluster = clusters[0]

        self.assertEqual(cluster.id, 'us-east-1')
        self.assertEqual(cluster.region.id, 'us-east')
        self.assertEqual(cluster.domain, 'us-east-1.linodeobjects.com')
        self.assertEqual(cluster.static_site_domain, 'website-us-east-1.linodeobjects.com')

    def test_get_keys(self):
        """
        Tests that you can retrieve Object Storage Keys
        """
        keys = self.client.object_storage.keys()

        self.assertEqual(len(keys), 2)
        key1 = keys[0]
        key2 = keys[1]

        self.assertEqual(key1.id, 1)
        self.assertEqual(key1.label, 'object-storage-key-1')
        self.assertEqual(key1.access_key, 'testAccessKeyHere123')
        self.assertEqual(key1.secret_key, '[REDACTED]')

        self.assertEqual(key2.id, 2)
        self.assertEqual(key2.label, 'object-storage-key-2')
        self.assertEqual(key2.access_key, 'testAccessKeyHere456')
        self.assertEqual(key2.secret_key, '[REDACTED]')

    def test_keys_create(self):
        """
        Tests that you can create Object Storage Keys
        """
        with self.mock_post('object-storage/keys/1') as m:
            keys = self.client.object_storage.keys_create('object-storage-key-1')

            self.assertIsNotNone(keys)
            self.assertEqual(keys.id, 1)
            self.assertEqual(keys.label, 'object-storage-key-1')

            self.assertEqual(m.call_url, '/object-storage/keys')
            self.assertEqual(m.call_data, {"label":"object-storage-key-1"})
