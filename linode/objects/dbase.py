from .base import Base
from linode import api

class DerivedBase(Base):
    """
    The DerivedBase class holds information about an object who belongs to another object
    (for example, a disk belongs to a linode).  These objects have their own endpoints,
    but they are below another object in the hierarchy (i.e. /linodes/lnde_123/disks/disk_123)
    """
    derived_url_path = '' #override in child classes

    def __init__(self, parent_id, parent_id_name='parent_id'):
        Base.__init__(self)

        self._set(parent_id_name, parent_id)

    @classmethod
    def _api_get_derived(cls, parent):
        base_url = "{}/{}".format(type(parent).api_endpoint, cls.derived_url_path)
         
        return api.get_objects(base_url, cls.derived_url_path, model=parent, parent_id=parent.id)
