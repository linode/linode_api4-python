from unittest import TestCase

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
