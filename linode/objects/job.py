from .dbase import DerivedBase
from .base import Property

class Job(DerivedBase):
    api_endpoint = '/linodes/{linode_id}/jobs/{id}'
    derived_url_path = 'jobs'
    parent_id_name = 'linode_id' #override in child classes

    properties = {
        "action": Property(),
        "duration": Property(volatile=True),
        "entered": Property(is_datetime=True),
        "finished": Property(volatile=True, is_datetime=True),
        "id": Property(identifier=True),
        "label": Property(),
        "message": Property(),
        "started": Property(volatile=True, is_datetime=True),
        "success": Property(volatile=True),
        "linode_id": Property(identifier=True),
    }
