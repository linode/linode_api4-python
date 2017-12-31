from __future__ import absolute_import

from linode.objects import DerivedBase, Property


class TicketReply(DerivedBase):
    api_endpoint = '/support/tickets/{ticket_id}/replies'
    derived_url_path = 'replies'
    parent_id_name='ticket_id'

    properties = {
        'id': Property(identifier=True),
        'ticket_id': Property(identifier=True),
        'description': Property(),
        'created': Property(is_datetime=True),
        'created_by': Property(),
        'from_linode': Property(),
    }
