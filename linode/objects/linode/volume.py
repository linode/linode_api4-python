from ...errors import UnexpectedResponseError
from .. import Base, Property, Region
from . import Linode

class Volume(Base):
    api_name = 'volumes'
    api_endpoint = '/linode/volumes/{id}'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'updated': Property(is_datetime=True),
        'linode_id': Property(id_relationship=Linode),
        'label': Property(mutable=True, filterable=True),
        'size': Property(filterable=True),
        'status': Property(filterable=True),
        'region': Property(relationship=Region),
    }
