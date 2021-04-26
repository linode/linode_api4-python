from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property


class FirewallDevice(DerivedBase):
    api_endpoint = '/networking/firewalls/{firewall_id}/devices/{id}'
    derived_url_path = 'devices'
    parent_id_name = 'firewall_id'

    properties = {
        'created': Property(filterable=True, is_datetime=True),
        'updated': Property(filterable=True, is_datetime=True),
        'entity': Property(),
        'id': Property(identifier=True)
    }


class Firewall(Base):
    """
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
    """

    api_endpoint = "/networking/firewalls/{id}"

    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'tags': Property(mutable=True, filterable=True),
        'status': Property(mutable=True),
        'created': Property(filterable=True, is_datetime=True),
        'updated': Property(filterable=True, is_datetime=True),
        'devices': Property(derived_class=FirewallDevice),
    }

    @property
    def rules(self):
        """
        Returns the JSON rules for this Firewall
        """
        return self._client.get('{}/rules'.format(self.api_endpoint), model=self)

    def update_rules(self, rules):
        """
        Sets the JSON rules for this Firewall
        """
        return self._client.put('{}/rules'.format(self.api_endpoint), model=self, data=rules)

    def device_create(self, id, type, **kwargs):
        """
        Creates and attaches a device to this Firewall

        :param id: The ID of the entity to create a device for.
        :type id: int

        :param type: The type of entity the device is being created for. (`linode`)
        :type type: str
        """
        params = {
            'id': id,
            'type': type,
        }
        params.update(kwargs)

        result = self._client.post("{}/devices".format(Firewall.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating device!', json=result)

        c = FirewallDevice(self._client, result['id'], self.id, result)
        return c
