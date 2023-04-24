from linode_api4.objects import Base, Property


class LongviewClient(Base):
    api_endpoint = "/longview/clients/{id}"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "label": Property(mutable=True, filterable=True),
        "install_code": Property(),
        "apps": Property(),
        "api_key": Property(),
    }


class LongviewSubscription(Base):
    api_endpoint = "/longview/subscriptions/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property(),
    }


class LongviewPlan(Base):
    api_endpoint = "/longview/plan"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property(),
    }

    def longview_plan_update(self, longview_subscription):
        """
        Update your Longview plan to that of the given subcription ID.

        :param longview_subscription: The subscription ID for a particular Longview plan.
                                      A value of null corresponds to Longview Free.
        :type longview_subscription: : str
        """

        if longview_subscription not in [
            "",
            "longview-3",
            "longview-10",
            "longview-40",
            "longview-100",
        ]:
            raise ValueError(
                "Invalid longview plan subscription: {}".format(
                    longview_subscription
                )
            )

        params = {"longview_subscription": longview_subscription}

        result = self._client.post(
            LongviewPlan.api_endpoint, model=self, data=params
        )
        self.invalidate()

        return LongviewPlan(self._client, result["id"], result)
