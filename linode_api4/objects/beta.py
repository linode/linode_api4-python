from linode_api4.objects import Base, Property


class BetaProgram(Base):
    """
    Beta program is a new product or service that's not generally available to all customers.
    User with permissions can enroll into a beta program and access the functionalities.

    API Documentation: https://www.linode.com/docs/api/beta-programs/#beta-program-view
    """

    api_endpoint = "/betas/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "description": Property(),
        "started": Property(is_datetime=True),
        "ended": Property(is_datetime=True),
        "greenlight_only": Property(),
        "more_info": Property(),
    }
