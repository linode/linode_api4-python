from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Account,
    AccountSettings,
    Event,
    Invoice,
    MappedObject,
    OAuthClient,
    Payment,
    User,
)


class AccountGroup(Group):
    """
    Collections related to your account.
    """

    def __call__(self):
        """
        Retrieves information about the acting user's account, such as billing
        information.  This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           account = client.account()

        API Documentation: https://www.linode.com/docs/api/account/#account-view

        :returns: Returns the acting user's account information.
        :rtype: Account
        """
        result = self.client.get("/account")

        if not "email" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting account!", json=result
            )

        return Account(self.client, result["email"], result)

    def events(self, *filters):
        """
        Lists events on the current account matching the given filters.

        API Documentation: https://www.linode.com/docs/api/account/#events-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of events on the current account matching the given filters.
        :rtype: PaginatedList of Event
        """

        return self.client._get_and_filter(Event, *filters)

    def events_mark_seen(self, event):
        """
        Marks event as the last event we have seen.  If event is an int, it is treated
        as an event_id, otherwise it should be an event object whose id will be used.

        API Documentation: https://www.linode.com/docs/api/account/#event-mark-as-seen

        :param event: The Linode event to mark as seen.
        :type event: Event or int
        """
        last_seen = event if isinstance(event, int) else event.id
        self.client.post(
            "{}/seen".format(Event.api_endpoint),
            model=Event(self.client, last_seen),
        )

    def settings(self):
        """
        Returns the account settings data for this acocunt.  This is not  a
        listing endpoint.

        API Documentation: https://www.linode.com/docs/api/account/#account-settings-view

        :returns: The account settings data for this account.
        :rtype: AccountSettings
        """
        result = self.client.get("/account/settings")

        if not "managed" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting account settings!",
                json=result,
            )

        s = AccountSettings(self.client, result["managed"], result)
        return s

    def invoices(self):
        """
        Returns Invoices issued to this account.

        API Documentation: https://www.linode.com/docs/api/account/#invoices-list

        :param filters: Any number of filters to apply to this query.

        :returns: Invoices issued to this account.
        :rtype: PaginatedList of Invoice
        """
        return self.client._get_and_filter(Invoice)

    def payments(self):
        """
        Returns a list of Payments made on this account.

        API Documentation: https://www.linode.com/docs/api/account/#payments-list

        :returns: A list of payments made on this account.
        :rtype: PaginatedList of Payment
        """
        return self.client._get_and_filter(Payment)

    def oauth_clients(self, *filters):
        """
        Returns the OAuth Clients associated with this account.

        API Documentation: https://www.linode.com/docs/api/account/#oauth-clients-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of OAuth Clients associated with this account.
        :rtype: PaginatedList of OAuthClient
        """
        return self.client._get_and_filter(OAuthClient, *filters)

    def oauth_client_create(self, name, redirect_uri, **kwargs):
        """
        Creates a new OAuth client.

        API Documentation: https://www.linode.com/docs/api/account/#oauth-client-create

        :param name: The name of this application.
        :type name: str
        :param redirect_uri: The location a successful log in from https://login.linode.com should be redirected to for this client.
        :type redirect_uri: str

        :returns: The created OAuth Client.
        :rtype: OAuthClient
        """
        params = {
            "label": name,
            "redirect_uri": redirect_uri,
        }
        params.update(kwargs)

        result = self.client.post("/account/oauth-clients", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating OAuth Client!", json=result
            )

        c = OAuthClient(self.client, result["id"], result)
        return c

    def users(self, *filters):
        """
        Returns a list of users on this account.

        API Documentation: https://www.linode.com/docs/api/account/#users-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of users on this account.
        :rtype: PaginatedList of User
        """
        return self.client._get_and_filter(User, *filters)

    def transfer(self):
        """
        Returns a MappedObject containing the account's transfer pool data.

        API Documentation: https://www.linode.com/docs/api/account/#network-utilization-view

        :returns: Information about this account's transfer pool data.
        :rtype: MappedObject
        """
        result = self.client.get("/account/transfer")

        if not "used" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting Transfer Pool!"
            )

        return MappedObject(**result)

    def user_create(self, email, username, restricted=True):
        """
        Creates a new user on your account.  If you create an unrestricted user,
        they will immediately be able to access everything on your account.  If
        you create a restricted user, you must grant them access to parts of your
        account that you want to allow them to manage (see :any:`User.grants` for
        details).

        The new user will receive an email inviting them to set up their password.
        This must be completed before they can log in.

        API Documentation: https://www.linode.com/docs/api/account/#user-create

        :param email: The new user's email address.  This is used to finish setting
                      up their user account.
        :type email: str
        :param username: The new user's unique username.  They will use this username
                         to log in.
        :type username: str
        :param restricted: If True, the new user must be granted access to parts of
                           the account before they can do anything.  If False, the
                           new user will immediately be able to manage the entire
                           account.  Defaults to True.
        :type restricted: True

        :returns The new User.
        :rtype: User
        """
        params = {
            "email": email,
            "username": username,
            "restricted": restricted,
        }
        result = self.client.post("/account/users", data=params)

        if not all(
            [c in result for c in ("email", "restricted", "username")]
        ):  # pylint: disable=use-a-generator
            raise UnexpectedResponseError(
                "Unexpected response when creating user!", json=result
            )

        u = User(self.client, result["username"], result)
        return u
