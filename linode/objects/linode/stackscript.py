from __future__ import absolute_import

from enum import Enum

from linode.objects import Base, Image, Property


class UserDefinedFieldType(Enum):
    text = 1
    select_one = 2
    select_many = 3

class UserDefinedField():
    def __init__(self, name, label, example, field_type, choices=None):
        self.name = name
        self.label = label
        self.example = example
        self.field_type = field_type
        self.choices = choices

    def __repr__(self):
        return "{}({}): {}".format(self.label, self.field_type.name, self.example)

class StackScript(Base):
    api_endpoint = '/linode/stackscripts/{id}'
    properties = {
        "user_defined_fields": Property(),
        "label": Property(mutable=True, filterable=True),
        "rev_note": Property(mutable=True),
        "usernam": Property(filterable=True),
        "user_gravatar_id": Property(),
        "is_public": Property(mutable=True, filterable=True),
        "created": Property(is_datetime=True),
        "deployments_active": Property(),
        "script": Property(mutable=True),
        "images": Property(mutable=True, filterable=True), # TODO make slug_relationship
        "deployments_total": Property(),
        "description": Property(mutable=True, filterable=True),
        "updated": Property(is_datetime=True),
    }

    def _populate(self, json):
        """
        Override the populate method to map user_defined_fields to
        fancy values
        """
        Base._populate(self, json)

        mapped_udfs = []
        for udf in self.user_defined_fields:
            t = UserDefinedFieldType.text
            choices = None
            if hasattr(udf, 'oneof'):
                t = UserDefinedFieldType.select_one
                choices = udf.oneof.split(',')
            elif hasattr(udf, 'manyof'):
                t = UserDefinedFieldType.select_many
                choices = udf.manyof.split(',')

            mapped_udfs.append(UserDefinedField(udf.name,
                    udf.label if hasattr(udf, 'label') else None,
                    udf.example if hasattr(udf, 'example') else None,
                    t, choices=choices))

        self._set('user_defined_fields', mapped_udfs)
        ndist = [ Image(self._client, d) for d in self.images ]
        self._set('images', ndist)

    def _serialize(self):
        dct = Base._serialize(self)
        dct['images'] = [ d.id for d in self.images ]
        return dct
