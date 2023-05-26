from linode_api4.objects import Base, Property


class Region(Base):
    """
    A Region. Regions correspond to individual data centers, each located in a different geographical area.

    API Documentation: https://www.linode.com/docs/api/regions/#region-view
    """

    api_endpoint = "/regions/{id}"
    properties = {
        "id": Property(identifier=True),
        "country": Property(),
        "capabilities": Property(),
        "status": Property(),
        "resolvers": Property(),
        "label": Property(),
    }
