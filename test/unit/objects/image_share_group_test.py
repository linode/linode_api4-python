from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    ImageShareGroup,
    ImageShareGroupImagesToAdd,
    ImageShareGroupImageToAdd,
    ImageShareGroupImageToUpdate,
    ImageShareGroupMemberToAdd,
    ImageShareGroupMemberToUpdate,
    ImageShareGroupToken,
)


class ImageShareGroupTest(ClientBaseCase):
    """
    Tests the methods of ImageShareGroup class
    """

    def test_get_sharegroup(self):
        """
        Tests that an Image Share Group is loaded correctly by ID
        """
        sharegroup = ImageShareGroup(self.client, 1234)

        self.assertEqual(sharegroup.id, 1234)
        self.assertEqual(
            sharegroup.description, "My group of images to share with my team."
        )
        self.assertEqual(sharegroup.images_count, 0)
        self.assertEqual(sharegroup.is_suspended, False)
        self.assertEqual(sharegroup.label, "My Shared Images")
        self.assertEqual(sharegroup.members_count, 0)
        self.assertEqual(
            sharegroup.uuid, "1533863e-16a4-47b5-b829-ac0f35c13278"
        )

    def test_update_sharegroup(self):
        """
        Tests that an Image Share Group can be updated
        """
        with self.mock_put("/images/sharegroups/1234") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.label = "Updated Sharegroup Label"
            sharegroup.description = "Updated description for my sharegroup."
            sharegroup.save()
            self.assertEqual(m.call_url, "/images/sharegroups/1234")
            self.assertEqual(
                m.call_data,
                {
                    "label": "Updated Sharegroup Label",
                    "description": "Updated description for my sharegroup.",
                },
            )

    def test_delete_sharegroup(self):
        """
        Tests that deleting an Image Share Group creates the correct api request
        """
        with self.mock_delete() as m:
            sharegroup = ImageShareGroup(self.client, 1234)
            sharegroup.delete()

            self.assertEqual(m.call_url, "/images/sharegroups/1234")

    def test_add_images_to_sharegroup(self):
        """
        Tests that Images can be added to an Image Share Group
        """
        with self.mock_post("/images/sharegroups/1234/images") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.add_images(
                ImageShareGroupImagesToAdd(
                    images=[
                        ImageShareGroupImageToAdd(id="private/123"),
                    ]
                )
            )

            self.assertEqual(m.call_url, "/images/sharegroups/1234/images")
            self.assertEqual(
                m.call_data,
                {
                    "images": [
                        {"id": "private/123"},
                    ]
                },
            )

    def test_get_image_shares_in_sharegroup(self):
        """
        Tests that Image Shares in an Image Share Group can be retrieved
        """
        with self.mock_get("/images/sharegroups/1234/images") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            images = sharegroup.get_image_shares()

            self.assertEqual(m.call_url, "/images/sharegroups/1234/images")
            self.assertEqual(len(images), 1)
            self.assertEqual(images[0].id, "shared/1")

    def test_update_image_in_sharegroup(self):
        """
        Tests that an Image shared in an Image Share Group can be updated
        """
        with self.mock_put("/images/sharegroups/1234/images/shared/1") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.update_image_share(
                ImageShareGroupImageToUpdate(image_share_id="shared/1")
            )

            self.assertEqual(
                m.call_url, "/images/sharegroups/1234/images/shared/1"
            )
            self.assertEqual(
                m.call_data,
                {
                    "image_share_id": "shared/1",
                },
            )

    def test_remove_image_from_sharegroup(self):
        """
        Tests that an Image can be removed from an Image Share Group
        """
        with self.mock_delete() as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.revoke_image_share("shared/1")

            self.assertEqual(
                m.call_url, "/images/sharegroups/1234/images/shared/1"
            )

    def test_add_members_to_sharegroup(self):
        """
        Tests that members can be added to an Image Share Group
        """
        with self.mock_post("/images/sharegroups/1234/members") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.add_member(
                ImageShareGroupMemberToAdd(
                    token="secrettoken",
                    label="New Member",
                )
            )

            self.assertEqual(m.call_url, "/images/sharegroups/1234/members")
            self.assertEqual(
                m.call_data,
                {
                    "token": "secrettoken",
                    "label": "New Member",
                },
            )

    def test_get_members_in_sharegroup(self):
        """
        Tests that members in an Image Share Group can be retrieved
        """
        with self.mock_get("/images/sharegroups/1234/members") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            members = sharegroup.get_members()

            self.assertEqual(m.call_url, "/images/sharegroups/1234/members")
            self.assertEqual(len(members), 1)
            self.assertEqual(
                members[0].token_uuid, "4591075e-4ba8-43c9-a521-928c3d4a135d"
            )

    def test_get_member_in_sharegroup(self):
        """
        Tests that a specific member in an Image Share Group can be retrieved
        """
        with self.mock_get("/images/sharegroups/1234/members/abc123") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            member = sharegroup.get_member("abc123")

            self.assertEqual(
                m.call_url, "/images/sharegroups/1234/members/abc123"
            )
            self.assertEqual(member.token_uuid, "abc123")

    def test_update_member_in_sharegroup(self):
        """
        Tests that a member in an Image Share Group can be updated
        """
        with self.mock_put("/images/sharegroups/1234/members/abc123") as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.update_member(
                ImageShareGroupMemberToUpdate(
                    token_uuid="abc123",
                    label="Updated Member Label",
                )
            )

            self.assertEqual(
                m.call_url, "/images/sharegroups/1234/members/abc123"
            )
            self.assertEqual(
                m.call_data,
                {
                    "label": "Updated Member Label",
                },
            )

    def test_remove_member_from_sharegroup(self):
        """
        Tests that a member can be removed from an Image Share Group
        """
        with self.mock_delete() as m:
            sharegroup = self.client.load(ImageShareGroup, 1234)
            sharegroup.remove_member("abc123")

            self.assertEqual(
                m.call_url, "/images/sharegroups/1234/members/abc123"
            )


class ImageShareGroupTokenTest(ClientBaseCase):
    """
    Tests the methods of ImageShareGroupToken class
    """

    def test_get_sharegroup_token(self):
        """
        Tests that an Image Share Group Token is loaded correctly by UUID
        """
        token = self.client.load(ImageShareGroupToken, "abc123")

        self.assertEqual(token.token_uuid, "abc123")
        self.assertEqual(token.label, "My Sharegroup Token")
        self.assertEqual(token.sharegroup_label, "A Sharegroup")
        self.assertEqual(
            token.sharegroup_uuid, "e1d0e58b-f89f-4237-84ab-b82077342359"
        )
        self.assertEqual(token.status, "active")
        self.assertEqual(
            token.valid_for_sharegroup_uuid,
            "e1d0e58b-f89f-4237-84ab-b82077342359",
        )

    def test_update_sharegroup_token(self):
        """
        Tests that an Image Share Group Token can be updated
        """
        with self.mock_put("/images/sharegroups/tokens/abc123") as m:
            token = self.client.load(ImageShareGroupToken, "abc123")
            token.label = "Updated Token Label"
            token.save()
            self.assertEqual(m.call_url, "/images/sharegroups/tokens/abc123")
            self.assertEqual(
                m.call_data,
                {
                    "label": "Updated Token Label",
                },
            )

    def test_delete_sharegroup_token(self):
        """
        Tests that deleting an Image Share Group Token creates the correct api request
        """
        with self.mock_delete() as m:
            token = ImageShareGroupToken(self.client, "abc123")
            token.delete()

            self.assertEqual(m.call_url, "/images/sharegroups/tokens/abc123")

    def test_sharegroup_token_get_sharegroup(self):
        """
        Tests that the Image Share Group associated with a Token can be retrieved
        """
        with self.mock_get("/images/sharegroups/tokens/abc123/sharegroup") as m:
            token = self.client.load(ImageShareGroupToken, "abc123")
            sharegroup = token.get_sharegroup()

            self.assertEqual(
                m.call_url, "/images/sharegroups/tokens/abc123/sharegroup"
            )
            self.assertEqual(sharegroup.id, 1234)

    def test_sharegroup_token_get_images(self):
        """
        Tests that the Images associated with a Token can be retrieved
        """
        with self.mock_get(
            "/images/sharegroups/tokens/abc123/sharegroup/images"
        ) as m:
            token = self.client.load(ImageShareGroupToken, "abc123")
            images = token.get_images()

            self.assertEqual(
                m.call_url,
                "/images/sharegroups/tokens/abc123/sharegroup/images",
            )
            self.assertEqual(len(images), 1)
            self.assertEqual(images[0].id, "shared/1")
