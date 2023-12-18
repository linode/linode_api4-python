from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import LongviewSubscription
from linode_api4.objects.beta import BetaProgram
from linode_api4.objects.linode import Instance
from linode_api4.objects.networking import IPAddress
from linode_api4.objects.object_storage import (
    ObjectStorageACL,
    ObjectStorageCluster,
)


class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """

    def test_get_no_empty_body(self):
        """
        Tests that a valid JSON body is passed for a GET call
        """
        with self.mock_get("linode/instances") as m:
            self.client.regions()

            self.assertEqual(m.call_data_raw, None)

    def test_get_account(self):
        a = self.client.account()
        self.assertEqual(a._populated, True)

        self.assertEqual(a.first_name, "Test")
        self.assertEqual(a.last_name, "Guy")
        self.assertEqual(a.email, "support@linode.com")
        self.assertEqual(a.phone, "123-456-7890")
        self.assertEqual(a.company, "Linode")
        self.assertEqual(a.address_1, "3rd & Arch St")
        self.assertEqual(a.address_2, "")
        self.assertEqual(a.city, "Philadelphia")
        self.assertEqual(a.state, "PA")
        self.assertEqual(a.country, "US")
        self.assertEqual(a.zip, "19106")
        self.assertEqual(a.tax_id, "")
        self.assertEqual(a.balance, 0)
        self.assertEqual(
            a.capabilities,
            ["Linodes", "NodeBalancers", "Block Storage", "Object Storage"],
        )

    def test_get_regions(self):
        r = self.client.regions()

        self.assertEqual(len(r), 11)
        for region in r:
            self.assertTrue(region._populated)
            self.assertIsNotNone(region.id)
            self.assertIsNotNone(region.country)
            if region.id in ("us-east", "eu-central", "ap-south"):
                self.assertEqual(
                    region.capabilities,
                    [
                        "Linodes",
                        "NodeBalancers",
                        "Block Storage",
                        "Object Storage",
                    ],
                )
            else:
                self.assertEqual(
                    region.capabilities,
                    ["Linodes", "NodeBalancers", "Block Storage"],
                )
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

        self.assertEqual(domain.domain, "example.org")
        self.assertEqual(domain.type, "master")
        self.assertEqual(domain.id, 12345)
        self.assertEqual(domain.axfr_ips, [])
        self.assertEqual(domain.retry_sec, 0)
        self.assertEqual(domain.ttl_sec, 300)
        self.assertEqual(domain.status, "active")
        self.assertEqual(
            domain.master_ips,
            [],
        )
        self.assertEqual(
            domain.description,
            "",
        )
        self.assertEqual(
            domain.group,
            "",
        )
        self.assertEqual(
            domain.expire_sec,
            0,
        )
        self.assertEqual(
            domain.soa_email,
            "test@example.org",
        )
        self.assertEqual(domain.refresh_sec, 0)

    def test_image_create(self):
        """
        Tests that an Image can be created successfully
        """
        with self.mock_post("images/private/123") as m:
            i = self.client.image_create(654, "Test-Image", "This is a test")

            self.assertIsNotNone(i)
            self.assertEqual(i.id, "private/123")
            self.assertEqual(i.capabilities[0], "cloud-init")

            self.assertEqual(m.call_url, "/images")

            self.assertEqual(
                m.call_data,
                {
                    "disk_id": 654,
                    "label": "Test-Image",
                    "description": "This is a test",
                },
            )

    def test_get_volumes(self):
        v = self.client.volumes()

        self.assertEqual(len(v), 3)
        self.assertEqual(v[0].label, "block1")
        self.assertEqual(v[0].region.id, "us-east-1a")
        self.assertEqual(v[1].label, "block2")
        self.assertEqual(v[1].size, 100)
        self.assertEqual(v[2].size, 200)
        self.assertEqual(v[2].label, "block3")
        self.assertEqual(v[0].filesystem_path, "this/is/a/file/path")
        self.assertEqual(v[0].hardware_type, "hdd")
        self.assertEqual(v[1].filesystem_path, "this/is/a/file/path")
        self.assertEqual(v[1].linode_label, None)
        self.assertEqual(v[2].filesystem_path, "this/is/a/file/path")
        self.assertEqual(v[2].hardware_type, "nvme")

        assert v[0].tags == ["something"]
        assert v[1].tags == []
        assert v[2].tags == ["attached"]

    def test_get_tags(self):
        """
        Tests that a list of Tags can be retrieved as expected
        """
        t = self.client.tags()

        self.assertEqual(len(t), 2)
        self.assertEqual(t[0].label, "nothing")
        self.assertEqual(t[1].label, "something")

    def test_tag_create(self):
        """
        Tests that creating a tag works as expected
        """
        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({"label": "nothing"}) as m:
            t = self.client.tag_create("nothing")

            self.assertIsNotNone(t)
            self.assertEqual(t.label, "nothing")

            self.assertEqual(m.call_url, "/tags")
            self.assertEqual(
                m.call_data,
                {
                    "label": "nothing",
                },
            )

    def test_tag_create_with_ids(self):
        """
        Tests that creating a tag with IDs sends the correct request
        """
        instance1, instance2 = self.client.linode.instances()[:2]
        domain1 = self.client.domains().first()
        nodebalancer1, nodebalancer2 = self.client.nodebalancers()[:2]
        volume1, volume2 = self.client.volumes()[:2]

        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({"label": "pytest"}) as m:
            t = self.client.tag_create(
                "pytest",
                instances=[instance1.id, instance2],
                nodebalancers=[nodebalancer1.id, nodebalancer2],
                domains=[domain1.id],
                volumes=[volume1.id, volume2],
            )

            self.assertIsNotNone(t)
            self.assertEqual(t.label, "pytest")

            self.assertEqual(m.call_url, "/tags")
            self.assertEqual(
                m.call_data,
                {
                    "label": "pytest",
                    "linodes": [instance1.id, instance2.id],
                    "domains": [domain1.id],
                    "nodebalancers": [nodebalancer1.id, nodebalancer2.id],
                    "volumes": [volume1.id, volume2.id],
                },
            )

    def test_tag_create_with_entities(self):
        """
        Tests that creating a tag with entities sends the correct request
        """
        instance1, instance2 = self.client.linode.instances()[:2]
        domain = self.client.domains().first()
        nodebalancer = self.client.nodebalancers().first()
        volume = self.client.volumes().first()

        # tags don't work like a normal RESTful collection, so we have to do this
        with self.mock_post({"label": "pytest"}) as m:
            t = self.client.tag_create(
                "pytest",
                entities=[instance1, domain, nodebalancer, volume, instance2],
            )

            self.assertIsNotNone(t)
            self.assertEqual(t.label, "pytest")

            self.assertEqual(m.call_url, "/tags")
            self.assertEqual(
                m.call_data,
                {
                    "label": "pytest",
                    "linodes": [instance1.id, instance2.id],
                    "domains": [domain.id],
                    "nodebalancers": [nodebalancer.id],
                    "volumes": [volume.id],
                },
            )

    def test_override_ca(self):
        """
        Tests that the CA file used for API requests can be overridden.
        """
        self.client.ca_path = "foobar"

        called = False

        old_get = self.client.session.get

        def get_mock(*params, verify=True, **kwargs):
            nonlocal called
            called = True
            assert verify == "foobar"
            return old_get(*params, **kwargs)

        self.client.session.get = get_mock

        self.client.linode.instances()

        assert called

    def test_custom_verify(self):
        """
        If we set a custom `verify` value on our session,
        we want it preserved.
        """
        called = False

        self.client.session.verify = False
        old_get = self.client.session.get

        def get_mock(*params, verify=True, **kwargs):
            nonlocal called
            called = True
            assert verify is False
            return old_get(*params, **kwargs)

        self.client.session.get = get_mock

        self.client.linode.instances()

        assert called


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
        self.assertEqual(s.longview_subscription.id, "longview-100")
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
        self.assertEqual(invoice.label, "Invoice #123456")
        self.assertEqual(invoice.total, 9.51)

    def test_logins(self):
        """
        Tests that logins can be retrieved
        """
        logins = self.client.account.logins()
        self.assertEqual(len(logins), 1)
        self.assertEqual(logins[0].id, 1234)

    def test_maintenance(self):
        """
        Tests that maintenance can be retrieved
        """
        with self.mock_get("/account/maintenance") as m:
            result = self.client.account.maintenance()
            self.assertEqual(m.call_url, "/account/maintenance")
            self.assertEqual(len(result), 1)
            self.assertEqual(
                result[0].reason,
                "This maintenance will allow us to update the BIOS on the host's motherboard.",
            )

    def test_notifications(self):
        """
        Tests that notifications can be retrieved
        """
        with self.mock_get("/account/notifications") as m:
            result = self.client.account.notifications()
            self.assertEqual(m.call_url, "/account/notifications")
            self.assertEqual(len(result), 1)
            self.assertEqual(
                result[0].label, "You have an important ticket open!"
            )

    def test_payment_methods(self):
        """
        Tests that payment methods can be retrieved
        """
        paymentMethods = self.client.account.payment_methods()
        self.assertEqual(len(paymentMethods), 1)
        self.assertEqual(paymentMethods[0].id, 123)

    def test_add_payment_method(self):
        """
        Tests that adding a payment method creates the correct api request.
        """
        with self.mock_post({}) as m:
            self.client.account.add_payment_method(
                {
                    "card_number": "123456789100",
                    "expiry_month": 1,
                    "expiry_year": 2028,
                    "cvv": 111,
                },
                True,
                "credit_card",
            )
            self.assertEqual(m.call_url, "/account/payment-methods")
            self.assertEqual(m.call_data["type"], "credit_card")
            self.assertTrue(m.call_data["is_default"])
            self.assertIsNotNone(m.call_data["data"])

    def test_add_promo_code(self):
        """
        Tests that adding a promo code creates the correct api request.
        """
        with self.mock_post("/account/promo-codes") as m:
            self.client.account.add_promo_code("123promo456")
            self.assertEqual(m.call_url, "/account/promo-codes")
            self.assertEqual(m.call_data["promo_code"], "123promo456")

    def test_service_transfers(self):
        """
        Tests that service transfers can be retrieved
        """
        serviceTransfers = self.client.account.service_transfers()
        self.assertEqual(len(serviceTransfers), 1)
        self.assertEqual(
            serviceTransfers[0].token, "123E4567-E89B-12D3-A456-426614174000"
        )

    def test_linode_managed_enable(self):
        """
        Tests that enabling linode managed creates the correct api request.
        """
        with self.mock_post({}) as m:
            self.client.account.linode_managed_enable()
            self.assertEqual(m.call_url, "/account/settings/managed-enable")

    def test_service_transfer_create(self):
        """
        Tests that creating a service transfer creates the correct api request.
        """
        data = {"linodes": [111, 222]}
        response = {
            "created": "2021-02-11T16:37:03",
            "entities": {"linodes": [111, 222]},
            "expiry": "2021-02-12T16:37:03",
            "is_sender": True,
            "status": "pending",
            "token": "123E4567-E89B-12D3-A456-426614174000",
            "updated": "2021-02-11T16:37:03",
        }

        with self.mock_post(response) as m:
            self.client.account.service_transfer_create(data)
            self.assertEqual(m.call_url, "/account/service-transfers")
            self.assertEqual(m.call_data["entities"], data)

    def test_payments(self):
        """
        Tests that payments can be retrieved
        """
        p = self.client.account.payments()

        self.assertEqual(len(p), 1)
        payment = p[0]

        self.assertEqual(payment.id, 123456)
        self.assertEqual(payment.date, datetime(2015, 1, 1, 5, 1, 2))
        self.assertEqual(payment.usd, 1000)

    def test_enrolled_betas(self):
        """
        Tests that enrolled beta programs can be retrieved
        """
        enrolled_betas = self.client.account.enrolled_betas()

        self.assertEqual(len(enrolled_betas), 1)
        beta = enrolled_betas[0]

        self.assertEqual(beta.id, "cool")
        self.assertEqual(beta.enrolled, datetime(2018, 1, 2, 3, 4, 5))
        self.assertEqual(beta.started, datetime(2018, 1, 2, 3, 4, 5))
        self.assertEqual(beta.ended, datetime(2018, 1, 2, 3, 4, 5))

    def test_join_beta_program(self):
        """
        Tests that user can join a beta program
        """
        join_beta_url = "/account/betas"
        with self.mock_post({}) as m:
            self.client.account.join_beta_program("cool_beta")
            self.assertEqual(
                m.call_data,
                {
                    "id": "cool_beta",
                },
            )
            self.assertEqual(m.call_url, join_beta_url)

        # Test that user can join a beta program with an BetaProgram object
        with self.mock_post({}) as m:
            self.client.account.join_beta_program(
                BetaProgram(self.client, "cool_beta")
            )
            self.assertEqual(
                m.call_data,
                {
                    "id": "cool_beta",
                },
            )
            self.assertEqual(m.call_url, join_beta_url)

    def test_account_transfer(self):
        """
        Tests that payments can be retrieved
        """
        transfer = self.client.account.transfer()

        self.assertEqual(transfer.quota, 471)
        self.assertEqual(transfer.used, 737373)
        self.assertEqual(transfer.billable, 0)

        self.assertEqual(len(transfer.region_transfers), 1)
        self.assertEqual(transfer.region_transfers[0].id, "ap-west")
        self.assertEqual(transfer.region_transfers[0].used, 1)
        self.assertEqual(transfer.region_transfers[0].quota, 5010)
        self.assertEqual(transfer.region_transfers[0].billable, 0)

    def test_account_availabilities(self):
        """
        Tests that account availabilities can be retrieved
        """
        availabilities = self.client.account.availabilities()

        self.assertEqual(len(availabilities), 11)
        availability = availabilities[0]

        self.assertEqual(availability.region, "ap-west")
        self.assertEqual(availability.unavailable, [])


class BetaProgramGroupTest(ClientBaseCase):
    """
    Tests methods of the BetaProgramGroup
    """

    def test_betas(self):
        """
        Test that available beta programs can be retrieved
        """
        betas = self.client.beta.betas()

        self.assertEqual(len(betas), 2)
        beta = betas[0]
        self.assertEqual(beta.id, "active_closed")
        self.assertEqual(beta.label, "active closed beta")
        self.assertEqual(beta.started, datetime(2023, 7, 19, 15, 23, 43))
        self.assertEqual(beta.ended, None)
        self.assertEqual(beta.greenlight_only, True)
        self.assertEqual(beta.more_info, "a link with even more info")


class LinodeGroupTest(ClientBaseCase):
    """
    Tests methods of the LinodeGroup
    """

    def test_instance_create(self):
        """
        Tests that a Linode Instance can be created successfully
        """
        with self.mock_post("linode/instances/123") as m:
            l = self.client.linode.instance_create(
                "g5-standard-1", "us-east-1a"
            )

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, "/linode/instances")

            self.assertEqual(
                m.call_data, {"region": "us-east-1a", "type": "g5-standard-1"}
            )

    def test_instance_create_with_image(self):
        """
        Tests that a Linode Instance can be created with an image, and a password generated
        """
        with self.mock_post("linode/instances/123") as m:
            l, pw = self.client.linode.instance_create(
                "g5-standard-1", "us-east-1a", image="linode/debian9"
            )

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, "/linode/instances")

            self.assertEqual(
                m.call_data,
                {
                    "region": "us-east-1a",
                    "type": "g5-standard-1",
                    "image": "linode/debian9",
                    "root_pass": pw,
                },
            )


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
        with self.mock_post("longview/clients/5678") as m:
            client = self.client.longview.client_create()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, "longview5678")

            self.assertEqual(m.call_url, "/longview/clients")
            self.assertEqual(m.call_data, {})

    def test_client_create_with_label(self):
        """
        Tests that creating a client with a label calls the api correctly
        """
        with self.mock_post("longview/clients/1234") as m:
            client = self.client.longview.client_create(label="test_client_1")

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 1234)
            self.assertEqual(client.label, "test_client_1")

            self.assertEqual(m.call_url, "/longview/clients")
            self.assertEqual(m.call_data, {"label": "test_client_1"})

    def test_update_plan(self):
        """
        Tests that you can submit a correct longview plan update api request
        """
        with self.mock_post("/longview/plan") as m:
            result = self.client.longview.longview_plan_update("longview-100")
            self.assertEqual(m.call_url, "/longview/plan")
            self.assertEqual(
                m.call_data["longview_subscription"], "longview-100"
            )
            self.assertEqual(result.id, "longview-10")
            self.assertEqual(result.clients_included, 10)
            self.assertEqual(result.label, "Longview Pro 10 pack")
            self.assertIsNotNone(result.price)

    def test_get_subscriptions(self):
        """
        Tests that Longview subscriptions can be retrieved
        """

        with self.mock_get("longview/subscriptions") as m:
            r = self.client.longview.subscriptions()
            self.assertEqual(m.call_url, "/longview/subscriptions")

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


class LKEGroupTest(ClientBaseCase):
    """
    Tests methods of the LKEGroupTest
    """

    def test_kube_version(self):
        """
        Tests that KubeVersions can be retrieved
        """
        versions = self.client.lke.versions()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].id, "1.19")
        self.assertEqual(versions[1].id, "1.18")
        self.assertEqual(versions[2].id, "1.17")

    def test_cluster_create_with_api_objects(self):
        """
        Tests clusters can be created using api objects
        """
        region = self.client.regions().first()
        node_type = self.client.linode.types()[0]
        version = self.client.lke.versions()[0]
        node_pools = self.client.lke.node_pool(node_type, 3)
        with self.mock_post("lke/clusters") as m:
            cluster = self.client.lke.cluster_create(
                region, "example-cluster", node_pools, version
            )
            self.assertEqual(m.call_data["region"], "ap-west")
            self.assertEqual(
                m.call_data["node_pools"], [{"type": "g5-nanode-1", "count": 3}]
            )
            self.assertEqual(m.call_data["k8s_version"], "1.19")

        self.assertEqual(cluster.id, 18881)
        self.assertEqual(cluster.region.id, "ap-west")
        self.assertEqual(cluster.k8s_version.id, "1.19")

    def test_cluster_create_with_string_repr(self):
        """
        Tests clusters can be created using string representations
        """
        with self.mock_post("lke/clusters") as m:
            cluster = self.client.lke.cluster_create(
                "ap-west",
                "example-cluster",
                {"type": "g6-standard-1", "count": 3},
                "1.19",
            )
            self.assertEqual(m.call_data["region"], "ap-west")
            self.assertEqual(
                m.call_data["node_pools"],
                [{"type": "g6-standard-1", "count": 3}],
            )
            self.assertEqual(m.call_data["k8s_version"], "1.19")

        self.assertEqual(cluster.id, 18881)
        self.assertEqual(cluster.region.id, "ap-west")
        self.assertEqual(cluster.k8s_version.id, "1.19")


class ProfileGroupTest(ClientBaseCase):
    """
    Tests methods of the ProfileGroup
    """

    def test_trusted_devices(self):
        devices = self.client.profile.trusted_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].id, 123)

    def test_logins(self):
        logins = self.client.profile.logins()
        self.assertEqual(len(logins), 1)
        self.assertEqual(logins[0].id, 123)

    def test_phone_number_delete(self):
        with self.mock_delete() as m:
            self.client.profile.phone_number_delete()
            self.assertEqual(m.call_url, "/profile/phone-number")

    def test_phone_number_verify(self):
        with self.mock_post({}) as m:
            self.client.profile.phone_number_verify("123456")
            self.assertEqual(m.call_url, "/profile/phone-number/verify")
            self.assertEqual(m.call_data["otp_code"], "123456")

    def test_phone_number_verification_code_send(self):
        with self.mock_post({}) as m:
            self.client.profile.phone_number_verification_code_send(
                "us", "1234567890"
            )
            self.assertEqual(m.call_url, "/profile/phone-number")
            self.assertEqual(m.call_data["iso_code"], "us")
            self.assertEqual(m.call_data["phone_number"], "1234567890")

    def test_user_preferences(self):
        with self.mock_get("/profile/preferences") as m:
            result = self.client.profile.user_preferences()
            self.assertEqual(m.call_url, "/profile/preferences")
            self.assertEqual(result.key1, "value1")
            self.assertEqual(result.key2, "value2")

    def test_user_preferences_update(self):
        with self.mock_put("/profile/preferences") as m:
            self.client.profile.user_preferences_update(
                key1="value3", key2="value4"
            )
            self.assertEqual(m.call_url, "/profile/preferences")
            self.assertEqual(m.call_data["key1"], "value3")
            self.assertEqual(m.call_data["key2"], "value4")

    def test_security_questions(self):
        with self.mock_get("/profile/security-questions") as m:
            result = self.client.profile.security_questions()
            self.assertEqual(m.call_url, "/profile/security-questions")
            self.assertEqual(result.security_questions[0].id, 1)
            self.assertEqual(
                result.security_questions[0].question,
                "In what city were you born?",
            )
            self.assertEqual(
                result.security_questions[0].response, "Gotham City"
            )

    def test_security_questions_answer(self):
        with self.mock_post("/profile/security-questions") as m:
            self.client.profile.security_questions_answer(
                [
                    {"question_id": 1, "response": "secret answer 1"},
                    {"question_id": 2, "response": "secret answer 2"},
                    {"question_id": 3, "response": "secret answer 3"},
                ]
            )
            self.assertEqual(m.call_url, "/profile/security-questions")

            self.assertEqual(
                m.call_data["security_questions"][0]["question_id"], 1
            )
            self.assertEqual(
                m.call_data["security_questions"][1]["question_id"], 2
            )
            self.assertEqual(
                m.call_data["security_questions"][2]["question_id"], 3
            )

    def test_get_sshkeys(self):
        """
        Tests that a list of SSH Keys can be retrieved
        """
        r = self.client.profile.ssh_keys()

        self.assertEqual(len(r), 2)

        key1, key2 = r

        self.assertEqual(key1.label, "Home Ubuntu PC")
        self.assertEqual(
            key1.created,
            datetime(year=2018, month=9, day=14, hour=13, minute=0, second=0),
        )
        self.assertEqual(key1.id, 22)
        self.assertEqual(
            key1.ssh_key,
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
            "CmhW7erNJNVxYjtzseGpBLmRRUTsT038w== dorthu@dorthu-command",
        )

    def test_client_create(self):
        """
        Tests that creating a client calls the api correctly
        """
        with self.mock_post("longview/clients/5678") as m:
            client = self.client.longview.client_create()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, "longview5678")

            self.assertEqual(m.call_url, "/longview/clients")
            self.assertEqual(m.call_data, {})

    def test_ssh_key_create(self):
        """
        Tests that creating an ssh key works as expected
        """
        with self.mock_post("profile/sshkeys/72") as m:
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
                "Work Laptop",
            )

            self.assertIsNotNone(key)
            self.assertEqual(key.id, 72)
            self.assertEqual(key.label, "Work Laptop")

            self.assertEqual(m.call_url, "/profile/sshkeys")
            self.assertEqual(
                m.call_data,
                {
                    "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDe9NlKepJsI/S98"
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
                    "label": "Work Laptop",
                },
            )


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

        self.assertEqual(cluster.id, "us-east-1")
        self.assertEqual(cluster.region.id, "us-east")
        self.assertEqual(cluster.domain, "us-east-1.linodeobjects.com")
        self.assertEqual(
            cluster.static_site_domain, "website-us-east-1.linodeobjects.com"
        )

    def test_get_keys(self):
        """
        Tests that you can retrieve Object Storage Keys
        """
        keys = self.client.object_storage.keys()

        self.assertEqual(len(keys), 2)
        key1 = keys[0]
        key2 = keys[1]

        self.assertEqual(key1.id, 1)
        self.assertEqual(key1.label, "object-storage-key-1")
        self.assertEqual(key1.access_key, "testAccessKeyHere123")
        self.assertEqual(key1.secret_key, "[REDACTED]")

        self.assertEqual(key2.id, 2)
        self.assertEqual(key2.label, "object-storage-key-2")
        self.assertEqual(key2.access_key, "testAccessKeyHere456")
        self.assertEqual(key2.secret_key, "[REDACTED]")

    def test_keys_create(self):
        """
        Tests that you can create Object Storage Keys
        """
        with self.mock_post("object-storage/keys/1") as m:
            keys = self.client.object_storage.keys_create(
                "object-storage-key-1"
            )

            self.assertIsNotNone(keys)
            self.assertEqual(keys.id, 1)
            self.assertEqual(keys.label, "object-storage-key-1")

            self.assertEqual(m.call_url, "/object-storage/keys")
            self.assertEqual(m.call_data, {"label": "object-storage-key-1"})

    def test_transfer(self):
        """
        Test that you can get the amount of outbound data transfer
        used by your account’s Object Storage buckets
        """
        object_storage_transfer_url = "/object-storage/transfer"

        with self.mock_get(object_storage_transfer_url) as m:
            result = self.client.object_storage.transfer()
            self.assertEqual(result.used, 12956600198)
            self.assertEqual(m.call_url, object_storage_transfer_url)

    def test_buckets(self):
        """
        Test that Object Storage Buckets can be reterived
        """
        object_storage_buckets_url = "/object-storage/buckets"

        with self.mock_get(object_storage_buckets_url) as m:
            buckets = self.client.object_storage.buckets()
            self.assertIsNotNone(buckets)
            bucket = buckets[0]

            self.assertEqual(m.call_url, object_storage_buckets_url)
            self.assertEqual(bucket.cluster, "us-east-1")
            self.assertEqual(
                bucket.created,
                datetime(
                    year=2019, month=1, day=1, hour=1, minute=23, second=45
                ),
            )
            self.assertEqual(
                bucket.hostname, "example-bucket.us-east-1.linodeobjects.com"
            )
            self.assertEqual(bucket.label, "example-bucket")
            self.assertEqual(bucket.objects, 4)
            self.assertEqual(bucket.size, 188318981)

    def test_bucket_create(self):
        """
        Test that you can create a Object Storage Bucket
        """
        # buckets don't work like a normal RESTful collection, so we have to do this
        with self.mock_post(
            {"label": "example-bucket", "cluster": "us-east-1"}
        ) as m:
            b = self.client.object_storage.bucket_create(
                "us-east-1", "example-bucket", ObjectStorageACL.PRIVATE, True
            )
            self.assertIsNotNone(b)
            self.assertEqual(m.call_url, "/object-storage/buckets")
            self.assertEqual(
                m.call_data,
                {
                    "label": "example-bucket",
                    "cluster": "us-east-1",
                    "cors_enabled": True,
                    "acl": "private",
                },
            )

        """
        Test that you can create a Object Storage Bucket passing a Cluster object
        """
        with self.mock_post(
            {"label": "example-bucket", "cluster": "us-east-1"}
        ) as m:
            cluster = ObjectStorageCluster(self.client, "us-east-1")
            b = self.client.object_storage.bucket_create(
                cluster, "example-bucket", "private", True
            )
            self.assertIsNotNone(b)
            self.assertEqual(m.call_url, "/object-storage/buckets")
            self.assertEqual(
                m.call_data,
                {
                    "label": "example-bucket",
                    "cluster": "us-east-1",
                    "cors_enabled": True,
                    "acl": "private",
                },
            )

    def test_object_url_create(self):
        """
        Test that you can create pre-signed URL to access a single Object in a bucket.
        """
        object_url_create_url = (
            "/object-storage/buckets/us-east-1/example-bucket/object-url"
        )
        with self.mock_post(object_url_create_url) as m:
            result = self.client.object_storage.object_url_create(
                "us-east-1", "example-bucket", "GET", "example"
            )
            self.assertIsNotNone(result)
            self.assertEqual(m.call_url, object_url_create_url)
            self.assertEqual(
                result.url,
                "https://us-east-1.linodeobjects.com/example-bucket/example?Signature=qr98TEucCntPgEG%2BsZQGDsJg93c%3D&Expires=1567609905&AWSAccessKeyId=G4YAF81XWY61DQM94SE0",
            )
            self.assertEqual(
                m.call_data,
                {
                    "method": "GET",
                    "name": "example",
                    "expires_in": 3600,
                },
            )


class NetworkingGroupTest(ClientBaseCase):
    """
    Tests for the NetworkingGroup
    """

    def test_get_vlans(self):
        """
        Tests that Object Storage Clusters can be retrieved
        """
        vlans = self.client.networking.vlans()

        self.assertEqual(len(vlans), 1)
        self.assertEqual(vlans[0].label, "vlan-test")
        self.assertEqual(vlans[0].region.id, "us-southeast")

        self.assertEqual(len(vlans[0].linodes), 2)
        self.assertEqual(vlans[0].linodes[0], 111)
        self.assertEqual(vlans[0].linodes[1], 222)

    def test_firewall_create(self):
        with self.mock_post("networking/firewalls/123") as m:
            rules = {
                "outbound": [],
                "outbound_policy": "DROP",
                "inbound": [],
                "inbound_policy": "DROP",
            }

            f = self.client.networking.firewall_create(
                "test-firewall-1", rules, status="enabled"
            )

            self.assertIsNotNone(f)

            self.assertEqual(m.call_url, "/networking/firewalls")
            self.assertEqual(m.method, "post")

            self.assertEqual(f.id, 123)
            self.assertEqual(
                m.call_data,
                {
                    "label": "test-firewall-1",
                    "status": "enabled",
                    "rules": rules,
                },
            )

    def test_get_firewalls(self):
        """
        Tests that firewalls can be retrieved
        """
        f = self.client.networking.firewalls()

        self.assertEqual(len(f), 1)
        firewall = f[0]

        self.assertEqual(firewall.id, 123)

    def test_ip_addresses_share(self):
        """
        Tests that you can submit a correct ip addresses share api request.
        """

        ip = IPAddress(self.client, "192.0.2.1", {})
        linode = Instance(self.client, 123)

        with self.mock_post({}) as m:
            self.client.networking.ip_addresses_share(["192.0.2.1"], 123)
            self.assertEqual(m.call_url, "/networking/ips/share")
            self.assertEqual(m.call_data["ips"], ["192.0.2.1"])
            self.assertEqual(m.call_data["linode_id"], 123)

        with self.mock_post({}) as m:
            self.client.networking.ip_addresses_share([ip], 123)
            self.assertEqual(m.call_url, "/networking/ips/share")
            self.assertEqual(m.call_data["ips"], ["192.0.2.1"])
            self.assertEqual(m.call_data["linode_id"], 123)

        with self.mock_post({}) as m:
            self.client.networking.ip_addresses_share(["192.0.2.1"], linode)
            self.assertEqual(m.call_url, "/networking/ips/share")
            self.assertEqual(m.call_data["ips"], ["192.0.2.1"])
            self.assertEqual(m.call_data["linode_id"], 123)

    def test_ip_addresses_assign(self):
        """
        Tests that you can submit a correct ip addresses assign api request.
        """

        with self.mock_post({}) as m:
            self.client.networking.ip_addresses_assign(
                {"assignments": [{"address": "192.0.2.1", "linode_id": 123}]},
                "us-east",
            )
            self.assertEqual(m.call_url, "/networking/ips/assign")
            self.assertEqual(
                m.call_data["assignments"],
                {"assignments": [{"address": "192.0.2.1", "linode_id": 123}]},
            )
            self.assertEqual(m.call_data["region"], "us-east")

    def test_ipv6_ranges(self):
        """
        Tests that IPRanges can be retrieved
        """
        ranges = self.client.networking.ipv6_ranges()
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0].range, "2600:3c01::")
