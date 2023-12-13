from typing import Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Account,
    AccountAvailability,
    AccountBetaProgram,
    AccountSettings,
    BetaProgram,
    Event,
    Invoice,
    Login,
    MappedObject,
    OAuthClient,
    Payment,
    PaymentMethod,
    ServiceTransfer,
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
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

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
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

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
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of users on this account.
        :rtype: PaginatedList of User
        """
        return self.client._get_and_filter(User, *filters)

    def logins(self):
        """
        Returns a collection of successful logins for all users on the account during the last 90 days.

        API Documentation: https://www.linode.com/docs/api/account/#user-logins-list-all

        :returns: A list of Logins on this account.
        :rtype: PaginatedList of Login
        """

        return self.client._get_and_filter(Login)

    def maintenance(self):
        """
        Returns a collection of Maintenance objects for any entity a user has permissions to view. Cancelled Maintenance objects are not returned.

        API Documentation: https://www.linode.com/docs/api/account/#user-logins-list-all

        :returns: A list of Maintenance objects on this account.
        :rtype: List of Maintenance objects as MappedObjects
        """

        result = self.client.get(
            "{}/maintenance".format(Account.api_endpoint), model=self
        )

        return [MappedObject(**r) for r in result["data"]]

    def payment_methods(self):
        """
        Returns a  list of Payment Methods for this Account.

        API Documentation: https://www.linode.com/docs/api/account/#payment-methods-list

        :returns: A list of Payment Methods on this account.
        :rtype: PaginatedList of PaymentMethod
        """

        return self.client._get_and_filter(PaymentMethod)

    def add_payment_method(self, data, is_default, type):
        """
        Adds a Payment Method to your Account with the option to set it as the default method.

        API Documentation: https://www.linode.com/docs/api/account/#payment-method-add

        :param data: An object representing the credit card information you have on file with
                     Linode to make Payments against your Account.
        :type data: dict

        Example usage::
           data = {
                "card_number": "4111111111111111",
                "expiry_month": 11,
                "expiry_year": 2020,
                "cvv": "111"
            }

        :param is_default: Whether this Payment Method is the default method for
                           automatically processing service charges.
        :type is_default: bool

        :param type: The type of Payment Method. Enum: ["credit_card]
        :type type: str
        """

        if type != "credit_card":
            raise ValueError("Unknown Payment Method type: {}".format(type))

        if (
            "card_number" not in data
            or "expiry_month" not in data
            or "expiry_year" not in data
            or "cvv" not in data
            or not data
        ):
            raise ValueError("Invalid credit card info provided")

        params = {"data": data, "type": type, "is_default": is_default}

        resp = self.client.post(
            "{}/payment-methods".format(Account.api_endpoint),
            model=self,
            data=params,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when adding payment method!",
                json=resp,
            )

    def notifications(self):
        """
        Returns a collection of Notification objects representing important, often time-sensitive items related to your Account.

        API Documentation: https://www.linode.com/docs/api/account/#notifications-list

        :returns: A list of Notifications on this account.
        :rtype: List of Notification objects as MappedObjects
        """

        result = self.client.get(
            "{}/notifications".format(Account.api_endpoint), model=self
        )

        return [MappedObject(**r) for r in result["data"]]

    def linode_managed_enable(self):
        """
        Enables Linode Managed for the entire account and sends a welcome email to the account’s associated email address.

        API Documentation: https://www.linode.com/docs/api/account/#linode-managed-enable
        """

        resp = self.client.post(
            "{}/settings/managed-enable".format(Account.api_endpoint),
            model=self,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when enabling Linode Managed!",
                json=resp,
            )

    def add_promo_code(self, promo_code):
        """
        Adds an expiring Promo Credit to your account.

        API Documentation: https://www.linode.com/docs/api/account/#promo-credit-add

        :param promo_code: The Promo Code.
        :type promo_code: str
        """

        params = {
            "promo_code": promo_code,
        }

        resp = self.client.post(
            "{}/promo-codes".format(Account.api_endpoint),
            model=self,
            data=params,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when adding Promo Code!",
                json=resp,
            )

    def service_transfers(self):
        """
        Returns a collection of all created and accepted Service Transfers for this account, regardless of the user that created or accepted the transfer.

        API Documentation: https://www.linode.com/docs/api/account/#service-transfers-list

        :returns: A list of Service Transfers on this account.
        :rtype: PaginatedList of ServiceTransfer
        """

        return self.client._get_and_filter(ServiceTransfer)

    def service_transfer_create(self, entities):
        """
        Creates a transfer request for the specified services.

        API Documentation: https://www.linode.com/docs/api/account/#service-transfer-create

        :param entities: A collection of the services to include in this transfer request, separated by type.
        :type entities: dict

        Example usage::
           entities = {
                "linodes": [
                    111,
                    222
                ]
            }
        """

        if not entities:
            raise ValueError("Entities must be provided!")

        bad_entries = [
            k for k, v in entities.items() if not isinstance(v, list)
        ]
        if len(bad_entries) > 0:
            raise ValueError(
                f"Got unexpected type for entity lists: {', '.join(bad_entries)}"
            )

        params = {"entities": entities}

        resp = self.client.post(
            "{}/service-transfers".format(Account.api_endpoint),
            model=self,
            data=params,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when creating Service Transfer!",
                json=resp,
            )

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

    def enrolled_betas(self, *filters):
        """
        Returns a list of all Beta Programs an account is enrolled in.

        API doc: https://www.linode.com/docs/api/beta-programs/#enrolled-beta-programs-list

        :returns: a list of Beta Programs.
        :rtype: PaginatedList of AccountBetaProgram
        """
        return self.client._get_and_filter(AccountBetaProgram, *filters)

    def join_beta_program(self, beta: Union[str, BetaProgram]):
        """
        Enrolls an account into a beta program.

        API doc: https://www.linode.com/docs/api/beta-programs/#beta-program-enroll

        :param beta: The object or id of a beta program to join.
        :type beta: BetaProgram or str

        :returns: A boolean indicating whether the account joined a beta program successfully.
        :rtype: bool
        """

        self.client.post(
            "/account/betas",
            data={"id": beta.id if isinstance(beta, BetaProgram) else beta},
        )

        return True

    def availabilities(self, *filters):
        """
        Returns a list of all available regions and the resources which are NOT available
        to the account.

        API doc: TBD

        :returns: a list of region availability information.
        :rtype: PaginatedList of AccountAvailability
        """
        return self.client._get_and_filter(AccountAvailability, *filters)
