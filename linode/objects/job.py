from .dbase import DerivedBase
from .base import Property

class Job(DerivedBase):
    api_endpoint = '/linodes/{linode_id}/jobs/{id}'
    derived_url_path = 'jobs'

    properties = {
        "action": Property(),
        "duration": Property(volatile=True),
        "entered": Property(),
        "finished": Property(volatile=True),
        "id": Property(identifier=True),
        "label": Property(),
        "message": Property(),
        "started": Property(volatile=True),
        "success": Property(volatile=True),
        "linode_id": Property(identifier=True),
    }

    def __init__(self, id, linode_id):
        DerivedBase.__init__(self, linode_id, parent_id_name='linode_id')

        self._set('id', id)

    def __repr__(self):
        return "Linode Job: {}".format(self.id)
