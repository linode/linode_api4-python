from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import Profile, ProfileLogin, SSHKey
from linode_api4.objects.profile import TrustedDevice


class SSHKeyTest(ClientBaseCase):
    """
    Tests methods of the SSHKey class
    """

    def test_get_ssh_key(self):
        """
        Tests that an SSHKey is loaded correctly by ID
        """
        key = SSHKey(self.client, 22)
        self.assertEqual(key._populated, False)

        self.assertEqual(key.label, "Home Ubuntu PC")
        self.assertEqual(key._populated, True)

        self.assertEqual(
            key.created,
            datetime(year=2018, month=9, day=14, hour=13, minute=0, second=0),
        )
        self.assertEqual(key.id, 22)
        self.assertEqual(
            key.ssh_key,
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

    def test_update_ssh_key(self):
        """
        Tests that an SSHKey can be updated
        """
        key = SSHKey(self.client, 22)

        key.label = "New Label"

        with self.mock_put("profile/sshkeys/22") as m:
            key.save()

            self.assertEqual(m.call_url, "/profile/sshkeys/22")
            self.assertEqual(m.call_data, {"label": "New Label"})

    def test_delete_ssh_key(self):
        """
        Tests that and SSHKey can be deleted
        """
        key = SSHKey(self.client, 22)

        with self.mock_delete() as m:
            key.delete()

            self.assertEqual(m.call_url, "/profile/sshkeys/22")


class ProfileTest(ClientBaseCase):
    """
    Tests methods of the Profile class
    """

    def test_get_profile(self):
        """
        Tests that a Profile is loaded correctly by ID
        """
        profile = Profile(self.client, "exampleUser")

        self.assertEqual(profile.username, "exampleUser")
        self.assertEqual(profile.authentication_type, "password")
        self.assertIsNotNone(profile.authorized_keys)
        self.assertEqual(profile.email, "example-user@gmail.com")
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.ip_whitelist_enabled)
        self.assertEqual(profile.lish_auth_method, "keys_only")
        self.assertIsNotNone(profile.referrals)
        self.assertFalse(profile.restricted)
        self.assertEqual(profile.timezone, "US/Eastern")
        self.assertTrue(profile.two_factor_auth)
        self.assertEqual(profile.uid, 1234)
        self.assertEqual(profile.verified_phone_number, "+5555555555")

    def test_get_trusted_device(self):
        device = TrustedDevice(self.client, 123)

        self.assertEqual(device.id, 123)
        self.assertEqual(
            device.user_agent,
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36 Vivaldi/2.1.1337.36\n",
        )

    def test_get_login(self):
        login = ProfileLogin(self.client, 123)

        self.assertEqual(login.id, 123)
        self.assertEqual(login.ip, "192.0.2.0")
        self.assertEqual(login.status, "successful")
        self.assertEqual(login.username, "example_user")
        self.assertTrue(login.restricted)
