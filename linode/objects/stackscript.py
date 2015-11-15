from .base import Base, Property
from linode.api import api_call

class StackScript(Base): 
    api_endpoint = '/stackscripts/{id}'
    properties = {
        "created": Property(),
        "label": Property(mutable=True),
        "script": Property(),
        "description": Property(mutable=True),
        "distributions": Property(relationship=True),
        "deployments_total": Property(),
        "is_public": Property(mutable=True),
        "revision_note": Property(),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id) 

    def __repr__(self):
        return "StackScript {}".format(self.id)
