from __future__ import absolute_import

from linode.objects import DerivedBase, Property


class InvoiceItem(DerivedBase):
    api_endpoint = '/account/invoices/{invoice_id}/items'
    derived_url_path = 'items'
    parent_id_name='invoice_id'

    # TODO - this object doesn't have its own ID .. this might need
    # special handling
    properties = {
        'invoice_id': Property(identifier=True),
        'unit_price': Property(),
        'label': Property(),
        'amount': Property(),
        'quantity': Property(),
        'from': Property(is_datetime=True),
        'to': Property(is_datetime=True),
        'type': Property(),
    }
