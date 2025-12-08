from typing import Optional

from linode_api4.groups import Group
from linode_api4.objects import (
    ImageShareGroup,
    ImageShareGroupImagesToAdd,
    ImageShareGroupToken,
)
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.util import drop_null_keys


class ImageShareGroupAPIGroup(Group):
    """
    Collections related to Private Image Sharing.

    NOTE: Private Image Sharing features are in beta and may not be generally available.
    """

    def __call__(self, *filters):
        """
        Retrieves a list of Image Share Groups created by the user (producer).
        You can filter this query to retrieve only Image Share Groups
        relevant to a specific query, for example::

           filtered_share_groups = client.sharegroups(
               ImageShareGroup.label == "my-label")

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroups

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Image Share Groups.
        :rtype: PaginatedList of ImageShareGroup
        """
        return self.client._get_and_filter(ImageShareGroup, *filters)

    def sharegroups_by_image_id(self, image_id: str):
        """
        Retrieves a list of Image Share Groups that share a specific Private Image.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-images-sharegroups-image

        :param image_id: The ID of the Image to query for.
        :type image_id: str

        :returns: A list of Image Share Groups sharing the specified Image.
        :rtype: PaginatedList of ImageShareGroup
        """
        return self.client._get_and_filter(
            ImageShareGroup, endpoint="/images/{}/sharegroups".format(image_id)
        )

    def tokens(self, *filters):
        """
        Retrieves a list of Image Share Group Tokens created by the user (consumer).
        You can filter this query to retrieve only Image Share Group Tokens
        relevant to a specific query, for example::

           filtered_share_group_tokens = client.sharegroups.tokens(
               ImageShareGroupToken.label == "my-label")

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-user-tokens

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Image Share Group Tokens.
        :rtype: PaginatedList of ImageShareGroupToken
        """
        return self.client._get_and_filter(ImageShareGroupToken, *filters)

    def create_sharegroup(
        self,
        label: Optional[str] = None,
        description: Optional[str] = None,
        images: Optional[ImageShareGroupImagesToAdd] = None,
    ):
        """
        Creates a new Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-sharegroups

        :param label: The label for the resulting Image Share Group.
        :type label: str
        :param description: The description for the new Image Share Group.
        :type description: str
        :param images: A list of Images to share in the new Image Share Group, formatted in JSON.
        :type images: Optional[ImageShareGroupImagesToAdd]

        :returns: The new Image Share Group.
        :rtype: ImageShareGroup
        """
        params = {
            "label": label,
            "description": description,
        }

        if images:
            params["images"] = images

        result = self.client.post(
            "/images/sharegroups",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        return ImageShareGroup(self.client, result["id"], result)

    def create_token(
        self, valid_for_sharegroup_uuid: str, label: Optional[str] = None
    ):
        """
        Creates a new Image Share Group Token and returns the token value.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-sharegroup-tokens

        :param valid_for_sharegroup_uuid: The UUID of the Image Share Group that this token will be valid for.
        :type valid_for_sharegroup_uuid: Optional[str]
        :param label: The label for the resulting Image Share Group Token.
        :type label: str

        :returns: The new Image Share Group Token object and the one-time use token itself.
        :rtype: (ImageShareGroupToken, str)
        """
        params = {"valid_for_sharegroup_uuid": valid_for_sharegroup_uuid}

        if label:
            params["label"] = label

        result = self.client.post(
            "/images/sharegroups/tokens",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        token_value = result.pop("token", None)
        token_obj = ImageShareGroupToken(
            self.client, result["token_uuid"], result
        )
        return token_obj, token_value
