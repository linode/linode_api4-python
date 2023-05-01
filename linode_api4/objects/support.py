from pathlib import Path
from typing import Union

import requests

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.objects import (
    Base,
    DerivedBase,
    Domain,
    Instance,
    Property,
    Volume,
)
from linode_api4.objects.nodebalancer import NodeBalancer


class TicketReply(DerivedBase):
    """
    A reply to a Support Ticket.

    API Documentation: https://www.linode.com/docs/api/support/#replies-list
    """

    api_endpoint = "/support/tickets/{ticket_id}/replies"
    derived_url_path = "replies"
    parent_id_name = "ticket_id"

    properties = {
        "id": Property(identifier=True),
        "ticket_id": Property(identifier=True),
        "description": Property(),
        "created": Property(is_datetime=True),
        "created_by": Property(),
        "from_linode": Property(),
    }


class SupportTicket(Base):
    """
    An objected representing a Linode Support Ticket.

    API Documentation: https://www.linode.com/docs/api/support/#replies-list
    """

    api_endpoint = "/support/tickets/{id}"
    properties = {
        "id": Property(identifier=True),
        "summary": Property(),
        "description": Property(),
        "status": Property(),
        "entity": Property(),
        "opened": Property(is_datetime=True),
        "closed": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "updated_by": Property(),
        "replies": Property(derived_class=TicketReply),
        "attachments": Property(),
        "closable": Property(),
        "gravatar_id": Property(),
        "opened_by": Property(),
    }

    @property
    def linode(self):
        """
        If applicable, the Linode referenced in this ticket.

        :returns: The Linode referenced in this ticket.
        :rtype: Optional[Instance]
        """

        if self.entity and self.entity.type == "linode":
            return Instance(self._client, self.entity.id)
        return None

    @property
    def domain(self):
        """
        If applicable, the Domain referenced in this ticket.

        :returns: The Domain referenced in this ticket.
        :rtype: Optional[Domain]
        """

        if self.entity and self.entity.type == "domain":
            return Domain(self._client, self.entity.id)
        return None

    @property
    def nodebalancer(self):
        """
        If applicable, the NodeBalancer referenced in this ticket.

        :returns: The NodeBalancer referenced in this ticket.
        :rtype: Optional[NodeBalancer]
        """

        if self.entity and self.entity.type == "nodebalancer":
            return NodeBalancer(self._client, self.entity.id)
        return None

    @property
    def volume(self):
        """
        If applicable, the Volume referenced in this ticket.

        :returns: The Volume referenced in this ticket.
        :rtype: Optional[Volume]
        """

        if self.entity and self.entity.type == "volume":
            return Volume(self._client, self.entity.id)
        return None

    def post_reply(self, description):
        """
        Adds a reply to an existing Support Ticket.

        API Documentation: https://www.linode.com/docs/api/support/#reply-create

        :param description: The content of this Support Ticket Reply.
        :type description: str

        :returns: The new TicketReply object.
        :rtype: Optional[TicketReply]
        """

        result = self._client.post(
            "{}/replies".format(SupportTicket.api_endpoint),
            model=self,
            data={
                "description": description,
            },
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating ticket reply!", json=result
            )

        r = TicketReply(self._client, result["id"], self.id, result)
        return r

    def upload_attachment(self, attachment: Union[Path, str]):
        """
        Uploads an attachment to an existing Support Ticket.

        API Documentation: https://www.linode.com/docs/api/support/#support-ticket-attachment-create

        :param attachment: A path to the file to upload as an attachment.
        :type attachment: str

        :returns: Whether the upload operation was successful.
        :rtype: bool
        """
        if not isinstance(attachment, Path):
            attachment = Path(attachment)

        if not attachment.exists():
            raise ValueError("File not exist, nothing to upload.")

        headers = {
            "Authorization": "Bearer {}".format(self._client.token),
        }

        with open(attachment, "rb") as f:
            result = requests.post(
                "{}{}/attachments".format(
                    self._client.base_url,
                    SupportTicket.api_endpoint.format(id=self.id),
                ),
                headers=headers,
                files={"file": f},
            )

        if not result.status_code == 200:
            errors = []
            j = result.json()
            if "errors" in j:
                errors = [e["reason"] for e in j["errors"]]
            raise ApiError("{}: {}".format(result.status_code, errors), json=j)

        return True

    def support_ticket_close(self):
        """
        Closes a Support Ticket.

        API Documentation: https://www.linode.com/docs/api/support/#support-ticket-close
        """

        self._client.post("{}/close".format(self.api_endpoint), model=self)
