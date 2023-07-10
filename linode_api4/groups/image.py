from typing import BinaryIO, Tuple

import requests

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, Image
from linode_api4.util import drop_null_keys


class ImageGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves a list of available Images, including public and private
        Images available to the acting user.  You can filter this query to
        retrieve only Images relevant to a specific query, for example::

           debian_images = client.images(
               Image.vendor == "debain")

        API Documentation: https://www.linode.com/docs/api/images/#images-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of available Images.
        :rtype: PaginatedList of Image
        """
        return self.client._get_and_filter(Image, *filters)

    def create(self, disk, label=None, description=None, cloud_init=False):
        """
        Creates a new Image from a disk you own.

        API Documentation: https://www.linode.com/docs/api/images/#image-create

        :param disk: The Disk to imagize.
        :type disk: Disk or int
        :param label: The label for the resulting Image (defaults to the disk's
                      label.
        :type label: str
        :param description: The description for the new Image.
        :type description: str
        :param cloud_init: Whether this Image supports cloud-init.
        :type cloud_init: bool

        :returns: The new Image.
        :rtype: Image
        """
        params = {
            "disk_id": disk.id if issubclass(type(disk), Base) else disk,
        }

        if label is not None:
            params["label"] = label

        if description is not None:
            params["description"] = description

        if cloud_init:
            params["cloud_init"] = cloud_init

        result = self.client.post("/images", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating an Image from disk {}".format(
                    disk
                )
            )

        return Image(self.client, result["id"], result)

    def create_upload(
        self,
        label: str,
        region: str,
        description: str = None,
        cloud_init: bool = False,
    ) -> Tuple[Image, str]:
        """
        Creates a new Image and returns the corresponding upload URL.

        API Documentation: https://www.linode.com/docs/api/images/#image-upload

        :param label: The label of the Image to create.
        :type label: str
        :param region: The region to upload to. Once the image has been created, it can be used in any region.
        :type region: str
        :param description: The description for the new Image.
        :type description: str
        :param cloud_init: Whether this Image supports cloud-init.
        :type cloud_init: bool

        :returns: A tuple containing the new image and the image upload URL.
        :rtype: (Image, str)
        """
        params = {"label": label, "region": region, "description": description}

        if cloud_init:
            params["cloud_init"] = cloud_init

        result = self.client.post("/images/upload", data=drop_null_keys(params))

        if "image" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating an Image upload URL"
            )

        result_image = result["image"]
        result_url = result["upload_to"]

        return Image(self.client, result_image["id"], result_image), result_url

    def upload(
        self, label: str, region: str, file: BinaryIO, description: str = None
    ) -> Image:
        """
        Creates and uploads a new image.

        API Documentation: https://www.linode.com/docs/api/images/#image-upload

        :param label: The label of the Image to create.
        :type label: str
        :param region: The region to upload to. Once the image has been created, it can be used in any region.
        :type region: str
        :param file: The BinaryIO object to upload to the image. This is generally obtained from open("myfile", "rb").
        :param description: The description for the new Image.
        :type description: str

        :returns: The resulting image.
        :rtype: Image
        """

        image, url = self.create_upload(label, region, description=description)

        requests.put(
            url,
            headers={"Content-Type": "application/octet-stream"},
            data=file,
        )

        image._api_get()

        return image
