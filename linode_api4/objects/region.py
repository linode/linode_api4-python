from linode_api4.objects import Base, Property


class Region(Base):
    api_endpoint = "/regions/{id}"
    properties = {
        'id': Property(identifier=True),
        'country': Property(filterable=True),
        'capabilities': Property(),
        'status': Property(),
        'resolvers': Property(),
    }
