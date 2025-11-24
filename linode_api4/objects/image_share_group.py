from dataclasses import dataclass
from typing import List, Optional

from linode_api4.objects import Base, MappedObject, Property
from linode_api4.objects.serializable import JSONObject


@dataclass
class ImageShareGroupImageToAdd(JSONObject):
    """
    Data representing an Image to add to an Image Share Group.
    """

    id: str
    label: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self):
        d = {"id": self.id}
        if self.label is not None:
            d["label"] = self.label
        if self.description is not None:
            d["description"] = self.description
        return d


@dataclass
class ImageShareGroupImagesToAdd(JSONObject):
    """
    Data representing a list of Images to add to an Image Share Group.
    """

    images: List[ImageShareGroupImageToAdd]


@dataclass
class ImageShareGroupImageToUpdate(JSONObject):
    """
    Data to update an Image shared in an Image Share Group.
    """

    image_share_id: str
    label: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self):
        d = {"image_share_id": self.image_share_id}
        if self.label is not None:
            d["label"] = self.label
        if self.description is not None:
            d["description"] = self.description
        return d


@dataclass
class ImageShareGroupMemberToAdd(JSONObject):
    """
    Data representing a Member to add to an Image Share Group.
    """

    token: str
    label: str


@dataclass
class ImageShareGroupMemberToUpdate(JSONObject):
    """
    Data to update a Member in an Image Share Group.
    """

    token_uuid: str
    label: str


class ImageShareGroup(Base):
    """
    An Image Share Group is a group to share private images with other users. This class is intended
    to be used by a Producer of an Image Share Group, and not a Consumer.

    NOTE: Private Image Sharing features are in beta and may not be generally available.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup
    """

    api_endpoint = "/images/sharegroups/{id}"

    properties = {
        "id": Property(identifier=True),
        "uuid": Property(),
        "label": Property(mutable=True),
        "description": Property(mutable=True),
        "is_suspended": Property(),
        "images_count": Property(),
        "members_count": Property(),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
    }

    def add_images(self, images: ImageShareGroupImagesToAdd):
        """
        Add private images to be shared in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-sharegroup-images

        :param images: A list of Images to share in the Image Share Group, formatted in JSON.
        :type images: ImageShareGroupImagesToAdd

        :returns: A list of the new Image shares.
        :rtype: List of MappedObject
        """
        params = {"images": [img.to_dict() for img in images.images]}

        result = self._client.post(
            "{}/images".format(self.api_endpoint), model=self, data=params
        )

        # Sync this object to reflect the new images added to the share group.
        self.invalidate()

        # Expect result to be a dict with a 'data' key
        image_list = result.get("data", [])
        return [MappedObject(**item) for item in image_list]

    def get_image_shares(self):
        """
        Retrieves a list of images shared in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-images

        :returns: A list of the Image shares.
        :rtype: List of MappedObject
        """
        result = self._client.get(
            "{}/images".format(self.api_endpoint),
            model=self,
        )
        image_list = result.get("data", [])
        return [MappedObject(**item) for item in image_list]

    def update_image_share(self, image: ImageShareGroupImageToUpdate):
        """
        Update the label and description of an Image shared in the Image Share Group.
        Note that the ID provided in the image parameter must be the shared ID of an
        Image already shared in the Image Share Group, not the private ID.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-sharegroup-imageshare

        :param image: The Image to update, formatted in JSON.
        :type image: ImageShareGroupImageToUpdate

        :returns: The updated Image share.
        :rtype: MappedObject
        """
        params = image.to_dict()

        result = self._client.put(
            "{}/images/{}".format(self.api_endpoint, image.image_share_id),
            model=self,
            data=params,
        )

        return MappedObject(**result)

    def revoke_image_share(self, image_share_id: str):
        """
        Revoke an Image shared in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-sharegroup-imageshare

        :param image_share_id: The ID of the Image share to revoke.
        :type image_share_id: str
        """
        self._client.delete(
            "{}/images/{}".format(self.api_endpoint, image_share_id), model=self
        )

        # Sync this object to reflect the revoked image share.
        self.invalidate()

    def add_member(self, member: ImageShareGroupMemberToAdd):
        """
        Add a Member to the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-sharegroup-members

        :param member: The Member to add, formatted in JSON.
        :type member: ImageShareGroupMemberToAdd

        :returns: The new Member.
        :rtype: MappedObject
        """
        params = {
            "token": member.token,
            "label": member.label,
        }

        result = self._client.post(
            "{}/members".format(self.api_endpoint), model=self, data=params
        )

        # Sync this object to reflect the new member added to the share group.
        self.invalidate()

        return MappedObject(**result)

    def get_members(self):
        """
        Retrieves a list of members in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-members

        :returns: List of members.
        :rtype: List of MappedObject
        """
        result = self._client.get(
            "{}/members".format(self.api_endpoint),
            model=self,
        )
        member_list = result.get("data", [])
        return [MappedObject(**item) for item in member_list]

    def get_member(self, token_uuid: str):
        """
        Get a Member in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-member-token

        :param token_uuid: The UUID of the token corresponding to the Member to retrieve.
        :type token_uuid: str

        :returns: The requested Member.
        :rtype: MappedObject
        """
        result = self._client.get(
            "{}/members/{}".format(self.api_endpoint, token_uuid), model=self
        )

        return MappedObject(**result)

    def update_member(self, member: ImageShareGroupMemberToUpdate):
        """
        Update the label of a Member in the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-member-token

        :param member: The Member to update, formatted in JSON.
        :type member: ImageShareGroupMemberToUpdate

        :returns: The updated Member.
        :rtype: MappedObject
        """
        params = {
            "label": member.label,
        }

        result = self._client.put(
            "{}/members/{}".format(self.api_endpoint, member.token_uuid),
            model=self,
            data=params,
        )

        return MappedObject(**result)

    def remove_member(self, token_uuid: str):
        """
        Remove a Member from the Image Share Group.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-sharegroup-member-token

        :param token_uuid: The UUID of the token corresponding to the Member to remove.
        :type token_uuid: str
        """
        self._client.delete(
            "{}/members/{}".format(self.api_endpoint, token_uuid), model=self
        )

        # Sync this object to reflect the removed member.
        self.invalidate()


class ImageShareGroupToken(Base):
    """
    An Image Share Group Token is a token that can be used to access the Images shared in an Image Share Group.
    This class is intended to be used by a Consumer of an Image Share Group, and not a Producer.

    NOTE: Private Image Sharing features are in beta and may not be generally available.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-token
    """

    api_endpoint = "/images/sharegroups/tokens/{token_uuid}"
    id_attribute = "token_uuid"
    properties = {
        "token_uuid": Property(identifier=True),
        "status": Property(),
        "label": Property(mutable=True),
        "valid_for_sharegroup_uuid": Property(),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
        "sharegroup_uuid": Property(),
        "sharegroup_label": Property(),
    }

    def get_sharegroup(self):
        """
        Gets details about the Image Share Group that this token provides access to.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-by-token

        :returns: The requested Image Share Group.
        :rtype: MappedObject
        """
        result = self._client.get(
            "{}/sharegroup".format(self.api_endpoint), model=self
        )

        return MappedObject(**result)

    def get_images(self):
        """
        Retrieves a paginated list of images shared in the Image Share Group that this token provides access to.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-sharegroup-images-by-token

        :returns: List of images.
        :rtype: List of MappedObject
        """
        result = self._client.get(
            "{}/sharegroup/images".format(self.api_endpoint),
            model=self,
        )
        image_list = result.get("data", [])
        return [MappedObject(**item) for item in image_list]
