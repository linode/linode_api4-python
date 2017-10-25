from unittest import TestCase, mock

from linode.objects.base import Base, Property


class Bar(Base):
    """
    A dummy object that can be a child of another object.
    """
    api_endpoint = "/bar/{id}"
    properties = {
        'id': Property(identifier=True),
        'value': Property()
    }


class Foo(Base):
    """
    A dummy object we will use to test methods of the Base class.
    """
    api_endpoint = "/foo/{id}"
    properties = {
        'filterable': Property(filterable=True),
        'id': Property(identifier=True),
        'something': Property(),
        'bar': Property(slug_relationship=Bar)
    }


class BaseClassTestCase(TestCase):
    """
    Tests the Base class by inheriting from it and asserting that things do what they should.
    """

    def setUp(self):
        self.bar_dict = {
            'id': 2,
            'value': 'abc'
        }

        self.foo_dict = {
            'filterable': 'value',
            'id': 1,
            'something': 'else',
            'bar': 2
        }
        self.foo = Foo(mock.Mock(), 1, self.foo_dict)

    def test_well_formed_foo(self):
        """
        Tests that passing in a valid dict like an api response returns an object with dot notation
        and the correct properties.
        """

        self.assertEqual(self.foo.id, 1)
        self.assertEqual(self.foo.filterable, 'value')
        self.assertEqual(self.foo.something, 'else')
        self.assertIsInstance(self.foo.bar, Bar)

        # Assert properties of slug related field
        self.assertEqual(self.foo.bar.id, 2)

    def test_foo_properties(self):
        """
        Tests that passing in a valid dict like an api response returns an object with a well formed
        properties dictionary
        """

        self.assertTrue(self.foo.properties['id'].identifier)
        self.assertTrue(self.foo.properties['filterable'].filterable)
        self.assertFalse(self.foo.properties['something'].filterable)
