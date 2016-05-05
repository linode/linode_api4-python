import math

class PaginatedList(object):
    def __init__(self, client, page_endpoint, page=[], max_pages=1, total_items=None,
            parent_id=None, key=None):
        self.client = client
        self.page_endpoint = page_endpoint
        self.key = key if key else page_endpoint
        self.page_size = len(page)
        self.max_pages = max_pages
        self.lists = [ None for i in range(0, self.max_pages) ]
        self.lists[0] = page
        self.objects_parent_id = parent_id
        self.cur = 0 # for being a generator

        self.total_items = total_items
        if not total_items:
            self.total_items = len(page)

    def first(self):
        return self[0]

    def last(self):
        return self[-1]

    def only(self):
        if len(self) == 1:
            return self[0]
        raise ValueError("List {} has more than one element!".format(self))

    def __repr__(self):
        return "PaginatedList ({} items)".format(self.total_items)

    def _load_page(self, page_number):
        from linode import mappings

        j = self.client.get("/{}?page={}".format(self.page_endpoint, page_number+1))

        if j['total_pages'] != self.max_pages or j['total_results'] != len(self):
            raise RuntimeError('List {} has changed since creation!'.format(self))

        l = mappings.make_list(j[self.key], self.client, parent_id=self.objects_parent_id)
        self.lists[page_number] = l

    def __getitem__(self, index):
        # this comes in here now, but we're hadling it elsewhere
        if isinstance(index, slice):
            return self._get_slice(index)

        # handle negative indexing
        if index < 0:
            index = len(self) + index
            if index < 0:
                raise IndexError('list index out of range')

        if index >= self.page_size * self.max_pages:
            raise IndexError('list index out of range')
        normalized_index = index % self.page_size
        target_page = math.ceil((index+1.0)/self.page_size)-1
        target_page = int(target_page)

        if not self.lists[target_page]:
            self._load_page(target_page)

        return self.lists[target_page][normalized_index]

    def __len__(self):
        return self.total_items

    def _get_slice(self, s):
        i = s.start if s.start else 0
        j = s.stop if s.stop else self.total_items

        if not s.step is None and not s.step == 1:
            raise NotImplementedError('TODO')

        if i < 0 and j < 0:
            i = len(self) + i
            j = len(self) + j

        if i < 0 and not s.stop:
            i = len(self) + i

        if j < 0 and not s.start:
            j = len(self) + j

        if i > j:
            raise NotImplementedError('TODO')

        if i < 0 or j < 0 or i > self.page_size * self.max_pages \
            or j > self.page_size * self.max_pages:
            raise IndexError('list index out of range')

        i_normalized = i % self.page_size
        j_normalized = j % self.page_size
        i_page = math.ceil((i+1)/self.page_size)-1
        j_page = math.ceil((j+1)/self.page_size)-1

        if not self.lists[i_page]:
            self._load_page(i_page)
        if not self.lists[j_page]:
            self._load_page(j_page)

        # if we're entirely in one list, this is easy
        if i_page == j_page:
            return self.lists[i_page][i_normalized:j_normalized]

        ret = self.lists[i_page][i_normalized:]

        for page in range(i_page, j_page):
            if not self.lists[page]:
                self._load_page(page)

            if page != i_page and page != j_page:
                ret += self.lists[page]

        ret += self.lists[j_page][:j_normalized]

        return ret

    def __setitem__(self, index, value):
        raise AttributeError('Assigning to indicies in paginated lists is not supported')

    def __delitem__(self, index, value):
        raise AttributeError('Assigning to indicies in paginated lists is not supported')

    def __next__(self):
        if self.cur < len(self):
            self.cur += 1
            return self[self.cur-1]
        else:
            raise StopIteration()
