from linode_api4.objects import Base, Property


class LongviewClient(Base):
    """
    A Longview Client that is accessible for use. Longview is Linode’s system data graphing service.

    API Documentation: https://www.linode.com/docs/api/longview/#longview-client-view
    """

    api_endpoint = "/longview/clients/{id}"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "label": Property(mutable=True),
        "install_code": Property(),
        "apps": Property(),
        "api_key": Property(),
    }


class LongviewSubscription(Base):
    """
    Contains the Longview Plan details for a specific subscription id.

    API Documentation: https://www.linode.com/docs/api/longview/#longview-subscription-view
    """

    api_endpoint = "/longview/subscriptions/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property(),
    }


class LongviewPlan(Base):
    """
    The current Longview Plan an account is using.

    API Documentation: https://www.linode.com/docs/api/longview/#longview-plan-view
    """

    api_endpoint = "/longview/plan"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property(),
    }
