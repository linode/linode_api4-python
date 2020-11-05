from linode_api4.objects import Base


class DerivedBase(Base):
    """
    The DerivedBase class holds information about an object who belongs to another object
    (for example, a disk belongs to a linode).  These objects have their own endpoints,
    but they are below another object in the hierarchy (i.e. /linodes/lnde_123/disks/disk_123)
    """
    derived_url_path = '' #override in child classes
    parent_id_name = 'parent_id' #override in child classes

    def __init__(self, client, id, parent_id, json={}):
        """
        Initializes the parent.

        Args:
            self: (todo): write your description
            client: (todo): write your description
            id: (str): write your description
            parent_id: (int): write your description
            json: (dict): write your description
        """
        Base.__init__(self, client, id, json=json)

        self._set(type(self).parent_id_name, parent_id)

    @classmethod
    def _api_get_derived(cls, parent, client):
        """
        Return the parent

        Args:
            cls: (todo): write your description
            parent: (todo): write your description
            client: (todo): write your description
        """
        base_url = "{}/{}".format(type(parent).api_endpoint, cls.derived_url_path)
         
        return client._get_objects(base_url, cls, model=parent, parent_id=parent.id)
