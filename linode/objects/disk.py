from .dbase import DerivedBase
from .base import Property

class Disk(DerivedBase):
    api_endpoint = '/linodes/{linode_id}/disks/{id}'
    derived_url_path = 'disks'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'label': Property(mutable=True, filterable=True),
        'size': Property(filterable=True),
        'state': Property(filterable=True),
        'filesystem': Property(),
        'updated': Property(is_datetime=True),
        'linode_id': Property(identifier=True),
    }


    def duplicate(self):
        result = self._client.post(Disk.api_endpoint, model=self, data={})

        if not 'id' in result:
            return result

        d = Disk(self._client, result['id'], self.linode_id)
        d._populate(result)
        return d


    def reset_root_password(self, root_password=None):
        rpass = root_password
        if not rpass:
            from linode.objects.linode import Linode
            rpass = Linode.generate_root_password()

        params = {
            'password': rpass,
        }

        result = self._client.post(Disk.api_endpoint, model=self, data=params)

        if not 'id' in result:
            if not root_password:
                return result, rpass
            return result

        self._populate(result)
        if not root_password:
            return True, rpass
        return True
