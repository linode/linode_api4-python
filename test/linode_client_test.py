from test.base import ClientBaseCase


class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """
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

    def test_get_volumes(self):
        v = self.client.get_volumes()

        self.assertEqual(len(v), 2)
        self.assertEqual(v[0].label, 'block1')
        self.assertEqual(v[0].region.id, 'us-east-1a')
        self.assertEqual(v[1].label, 'block2')
        self.assertEqual(v[1].size, 100)


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
