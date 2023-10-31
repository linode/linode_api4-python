from typing import Optional

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property, Region


class VPCSubnet(DerivedBase):
    """
    An instance of a VPC subnet.

    API Documentation: TODO
    """

    api_endpoint = "/vpcs/{vpc_id}/subnets/{id}"
    derived_url_path = "subnets"
    parent_id_name = "vpc_id"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "ipv4": Property(),
        "linodes": Property(),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
    }

    def _populate(self, json):
        """
        Map linodes more nicely while populating.
        """

        if json is None:
            return

        # Necessary to prevent a circular import
        from linode_api4.objects.linode import (  # pylint: disable=import-outside-toplevel
            Instance,
        )

        DerivedBase._populate(self, json)

        self._set(
            "linodes",
            [Instance(self._client, v) for v in json.get("linodes", [])],
        )


class VPC(Base):
    """
    An instance of a VPC.

    API Documentation: TODO
    """

    api_endpoint = "/vpcs/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "description": Property(mutable=True),
        "region": Property(slug_relationship=Region),
        "subnets": Property(derived_class=VPCSubnet),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
    }

    def subnet_create(
        self,
        label: str,
        ipv4: Optional[str] = None,
        **kwargs,
    ) -> VPCSubnet:
        """
        Creates a new Subnet object under this VPC.

        API Documentation: TODO

        :param label: The label of this subnet.
        :type label: str
        :param ipv4: The IPv4 range of this subnet in CIDR format.
        :type ipv4: str
        :param ipv6: The IPv6 range of this subnet in CIDR format.
        :type ipv6: str
        """
        params = {
            "label": label,
        }

        if ipv4 is not None:
            params["ipv4"] = ipv4

        params.update(kwargs)

        result = self._client.post(
            "{}/subnets".format(VPC.api_endpoint), model=self, data=params
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating Subnet", json=result
            )

        d = VPCSubnet(self._client, result["id"], self.id, result)
        return d
