from test.base import ClientBaseCase

from linode import LongviewSubscription


class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """
    def test_get_no_empty_body(self):
        """
        Tests that a valid JSON body is passed for a GET call
        """
        with self.mock_get('linode/instances') as m:
            self.client.get_regions()

            self.assertEqual(m.call_data_raw, None)


    def test_get_account(self):
        a = self.client.get_account()
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

    def test_get_regions(self):
        r = self.client.get_regions()

        self.assertEqual(len(r), 9)
        for region in r:
            self.assertTrue(region._populated)
            self.assertIsNotNone(region.id)
            self.assertIsNotNone(region.country)

    def test_get_images(self):
        r = self.client.get_images()

        self.assertEqual(len(r), 4)
        for image in r:
            self.assertTrue(image._populated)
            self.assertIsNotNone(image.id)

    def test_create_image(self):
        """
        Tests that an Image can be created successfully
        """
        with self.mock_post('images/private/123') as m:
            i = self.client.create_image(654, 'Test-Image', 'This is a test')

            self.assertIsNotNone(i)
            self.assertEqual(i.id, 'private/123')

            self.assertEqual(m.call_url, '/images')

            self.assertEqual(m.call_data, {
                "disk_id": 654,
                "label": "Test-Image",
                "description": "This is a test",
            })

    def test_get_volumes(self):
        v = self.client.get_volumes()

        self.assertEqual(len(v), 2)
        self.assertEqual(v[0].label, 'block1')
        self.assertEqual(v[0].region.id, 'us-east-1a')
        self.assertEqual(v[1].label, 'block2')
        self.assertEqual(v[1].size, 100)


class AccountGroupTest(ClientBaseCase):
    """
    Tests methods of the AccountGroup
    """
    def test_get_settings(self):
        """
        Tests that account settings can be retrieved.
        """
        s = self.client.account.get_settings()
        self.assertEqual(s._populated, True)

        self.assertEqual(s.network_helper, False)
        self.assertEqual(s.managed, False)
        self.assertEqual(type(s.longview_subscription), LongviewSubscription)
        self.assertEqual(s.longview_subscription.id, 'longview-100')


class LinodeGroupTest(ClientBaseCase):
    """
    Tests methods of the LinodeGroup
    """
    def test_create_linode(self):
        """
        Tests that a Linode can be created successfully
        """
        with self.mock_post('linode/instances/123') as m:
            l = self.client.linode.create_instance('g5-standard-1', 'us-east-1a')

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, '/linode/instances')

            self.assertEqual(m.call_data, {
                "region": "us-east-1a",
                "type": "g5-standard-1"
            })

    def test_create_linode_with_image(self):
        """
        Tests that a Linode can be created with an image, and a password generated
        """
        with self.mock_post('linode/instances/123') as m:
            l, pw = self.client.linode.create_instance(
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
        r = self.client.longview.get_clients()

        self.assertEqual(len(r), 2)
        self.assertEqual(r[0].label, "test_client_1")
        self.assertEqual(r[0].id, 1234)
        self.assertEqual(r[1].label, "longview5678")
        self.assertEqual(r[1].id, 5678)


    def test_create_client(self):
        """
        Tests that creating a client calls the api correctly
        """
        with self.mock_post('longview/clients/5678') as m:
            client = self.client.longview.create_client()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, 'longview5678')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {})


    def test_create_client_with_label(self):
        """
        Tests that creating a client with a label calls the api correctly
        """
        with self.mock_post('longview/clients/1234') as m:
            client = self.client.longview.create_client(label='test_client_1')

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 1234)
            self.assertEqual(client.label, 'test_client_1')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {"label": "test_client_1"})

    def test_get_subscriptions(self):
        """
        Tests that Longview subscriptions can be retrieved
        """
        r = self.client.longview.get_subscriptions()

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
