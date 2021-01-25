from unittest import TestCase
from unittest.mock import MagicMock, call

from linode_api4.paginated_list import PaginatedList


class PaginationSlicingTest(TestCase):
    def setUp(self):
        """
        Creates sample mocked lists for use in the test cases
        """
        self.normal_list = list(range(25))
        self.paginated_list = PaginatedList(None, None, page=self.normal_list,
                total_items=25)

    def test_slice_normal(self):
        """
        Tests that bounded, forward slices work as expected
        """
        slices = ( (1, 10), (10, 20), (5, 25), (0, 10) )

        for (start, stop) in slices:
            self.assertEqual(self.normal_list[start:stop],
                    self.paginated_list[start:stop])

    def test_slice_negative(self):
        """
        Tests that negative indexing works in slices
        """
        slices = ( (-10,-5), (-20, 20), (3, -10) )

        for (start, stop) in slices:
            self.assertEqual(self.normal_list[start:stop],
                    self.paginated_list[start:stop])

    def test_slice_no_lower_bound(self):
        """
        Tests that slices without lower bounds work
        """
        self.assertEqual(self.normal_list[:5], self.paginated_list[:5])

    def test_slice_no_upper_bound(self):
        """
        Tests that slices without upper bounds work
        """
        self.assertEqual(self.normal_list[5:], self.paginated_list[5:])

    def test_slice_boundless(self):
        """
        Tests that unbound slices work
        """
        self.assertEqual(self.normal_list[:], self.paginated_list[:])

    def test_slice_bad_negative_index(self):
        """
        Tests that an IndexError is raised when a bad negative index is given
        """
        with self.assertRaises(IndexError):
            self.paginated_list[:-30]

    def test_slice_bad_index(self):
        """
        Tests that out of bounds indexes in slices work
        """
        self.assertEqual(self.normal_list[30:], self.paginated_list[30:])

    def test_slice_unsupported_step(self):
        """
        Tests that steps outside of 1 raise a NotImplementedError
        """
        for step in ( -1, 0, 2, 3 ):
            with self.assertRaises(NotImplementedError):
                self.paginated_list[::step]

    def test_slice_backward_indexing(self):
        """
        Tests that backwards indexing works as expected
        """
        self.assertEqual(self.normal_list[10:5], self.paginated_list[10:5])


class PageLoadingTest(TestCase):
    def test_page_size_in_request(self):
        """
        Tests that the correct page_size is added to requests when loading subsequent pages
        """
        class Test():
            # the PaginatedList expects a model class here
            @classmethod
            def make_instance(*args, **kwargs):
                return Test()

        for i in (25, 100, 500):
            # these are the pages we're sending in to the mocked list
            first_page = [ Test()  for x in range(i) ]
            second_page = {
                "data": [{"id": 1}],
                "pages": 2,
                "page": 2,
                "results": i + 1,
            }

            # our mock client to intercept the requests and return the mocked info
            client = MagicMock()
            client.get = MagicMock(return_value=second_page)

            # let's do it!
            p = PaginatedList(client, "/test", page=first_page, max_pages=2, total_items=i+1)
            p[i] # load second page

            # and we called the next page URL with the correct page_size
            assert client.get.call_args == call("//test?page=2&page_size={}".format(i), filters=None)
