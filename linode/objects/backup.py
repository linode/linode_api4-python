from .dbase import DerivedBase
from .base import Property

class Backup(DerivedBase):
    api_name = 'backups'
    api_endpoint = '/linodes/{linode_id}/backups/{id}'
    derived_url_path = 'backups'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'create_dt': Property(is_datetime=True),
        'duration': Property(),
        'finish_dt': Property(is_datetime=True),
        'message': Property(),
        'status': Property(volatile=True),
        'type': Property(),
        'linode_id': Property(identifier=True),
        'label': Property(),
    }

    def restore_to(self, linode):
        result = self._client.post("{}/restore".format(Backup.api_endpoint), model=self,
            data={
                "linode": linode.id,
        })
        return True
