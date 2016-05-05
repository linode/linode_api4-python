from .base import Base, Property

from enum import Enum

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
    api_endpoint = '/stackscripts/{id}'
    properties = {
        "user_defined_fields": Property(),
        "label": Property(mutable=True, filterable=True),
        "customer_id": Property(),
        "rev_note": Property(mutable=True),
        "user_id": Property(),
        "is_public": Property(mutable=True, filterable=True),
        "created": Property(is_datetime=True),
        "deployments_active": Property(),
        "script": Property(mutable=True),
        "distributions": Property(relationship=True, mutable=True, filterable=True),
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

            mapped_udfs.append(UserDefinedField(udf.name, udf.label, udf.example, t, \
                    choices=choices))

        self._set('user_defined_fields', mapped_udfs)
        for d in self.distributions:
            d._set("_populated", False) # these come in as partials
