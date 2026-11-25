from test.unit.base import ClientBaseCase


class ImageTest(ClientBaseCase):
    """
    Tests methods of the ImageShareGroupAPIGroup class
    """

    def test_image_share_groups(self):
        """
        Test that Image Share Groups can be retrieved successfully.
        """
        sharegroups = self.client.sharegroups()
        self.assertEqual(len(sharegroups), 2)

        self.assertEqual(sharegroups[0].id, 1)
        self.assertEqual(
            sharegroups[0].description,
            "My group of images to share with my team.",
        )
        self.assertEqual(sharegroups[0].images_count, 0)
        self.assertEqual(sharegroups[0].is_suspended, False)
        self.assertEqual(sharegroups[0].label, "My Shared Images")
        self.assertEqual(sharegroups[0].members_count, 0)
        self.assertEqual(
            sharegroups[0].uuid, "1533863e-16a4-47b5-b829-ac0f35c13278"
        )

        self.assertEqual(sharegroups[1].id, 2)
        self.assertEqual(
            sharegroups[1].description,
            "My other group of images to share with my team.",
        )
        self.assertEqual(sharegroups[1].images_count, 1)
        self.assertEqual(sharegroups[1].is_suspended, False)
        self.assertEqual(sharegroups[1].label, "My other Shared Images")
        self.assertEqual(sharegroups[1].members_count, 3)
        self.assertEqual(
            sharegroups[1].uuid, "30ee6599-eb0f-478c-9e55-4073c6c24a39"
        )

    def test_image_share_groups_by_image_id(self):
        """
        Test that Image Share Groups where a given private image is currently shared can be retrieved successfully.
        """

        sharegroups = self.client.sharegroups.sharegroups_by_image_id(
            "private/1234"
        )
        self.assertEqual(len(sharegroups), 1)

        self.assertEqual(sharegroups[0].id, 1)
        self.assertEqual(
            sharegroups[0].description,
            "My group of images to share with my team.",
        )
        self.assertEqual(sharegroups[0].images_count, 1)
        self.assertEqual(sharegroups[0].is_suspended, False)
        self.assertEqual(sharegroups[0].label, "My Shared Images")
        self.assertEqual(sharegroups[0].members_count, 0)
        self.assertEqual(
            sharegroups[0].uuid, "1533863e-16a4-47b5-b829-ac0f35c13278"
        )

    def test_image_share_group_tokens(self):
        """
        Test that Image Share Group tokens can be retrieved successfully.
        """

        tokens = self.client.sharegroups.tokens()
        self.assertEqual(len(tokens), 1)

        self.assertEqual(
            tokens[0].token_uuid, "13428362-5458-4dad-b14b-8d0d4d648f8c"
        )
        self.assertEqual(tokens[0].label, "My Sharegroup Token")
        self.assertEqual(tokens[0].sharegroup_label, "A Sharegroup")
        self.assertEqual(
            tokens[0].sharegroup_uuid, "e1d0e58b-f89f-4237-84ab-b82077342359"
        )
        self.assertEqual(
            tokens[0].valid_for_sharegroup_uuid,
            "e1d0e58b-f89f-4237-84ab-b82077342359",
        )
        self.assertEqual(tokens[0].status, "active")

    def test_image_share_group_create(self):
        """
        Test that an Image Share Group can be created successfully.
        """

        with self.mock_post("/images/sharegroups/1234") as m:
            sharegroup = self.client.sharegroups.create_sharegroup(
                label="My Shared Images",
                description="My group of images to share with my team.",
            )

            assert m.call_url == "/images/sharegroups"

            self.assertEqual(
                m.call_data,
                {
                    "label": "My Shared Images",
                    "description": "My group of images to share with my team.",
                },
            )

            self.assertEqual(sharegroup.id, 1234)
            self.assertEqual(
                sharegroup.description,
                "My group of images to share with my team.",
            )
            self.assertEqual(sharegroup.images_count, 0)
            self.assertEqual(sharegroup.is_suspended, False)
            self.assertEqual(sharegroup.label, "My Shared Images")
            self.assertEqual(sharegroup.members_count, 0)
            self.assertEqual(
                sharegroup.uuid, "1533863e-16a4-47b5-b829-ac0f35c13278"
            )

    def test_image_share_group_token_create(self):
        """
        Test that an Image Share Group token can be created successfully.
        """

        with self.mock_post("/images/sharegroups/tokens/abc123") as m:
            token = self.client.sharegroups.create_token(
                label="My Sharegroup Token",
                valid_for_sharegroup_uuid="e1d0e58b-f89f-4237-84ab-b82077342359",
            )

            assert m.call_url == "/images/sharegroups/tokens"

            self.assertEqual(
                m.call_data,
                {
                    "label": "My Sharegroup Token",
                    "valid_for_sharegroup_uuid": "e1d0e58b-f89f-4237-84ab-b82077342359",
                },
            )

            self.assertEqual(token[0].token_uuid, "abc123")
            self.assertEqual(token[0].label, "My Sharegroup Token")
            self.assertEqual(token[0].sharegroup_label, "A Sharegroup")
            self.assertEqual(
                token[0].sharegroup_uuid, "e1d0e58b-f89f-4237-84ab-b82077342359"
            )
            self.assertEqual(
                token[0].valid_for_sharegroup_uuid,
                "e1d0e58b-f89f-4237-84ab-b82077342359",
            )
            self.assertEqual(token[0].status, "active")
            self.assertEqual(token[1], "asupersecrettoken")
