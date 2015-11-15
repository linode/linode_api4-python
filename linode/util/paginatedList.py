import math

class PaginatedList(object):
    def __init__(self, page_endpoint, page=[], max_pages=1, total_items=None):
        self.page_endpoint = page_endpoint
        self.page_size = len(page) 
        self.max_pages = max_pages
        self.lists = [ None for i in range(0, self.max_pages) ]
        self.lists[0] = page 

        self.total_items = total_items
        if not total_items:
            self.total_items = len(page)

    def _load_page(self, page_number):
        from linode.api import api_call
        from linode import mappings

        print("Loading page {}".format(page_number))  
        j = api_call("/{}?page={}".format(self.page_endpoint, page_number+1))
        l = mappings.make_list(j[self.page_endpoint])
        self.lists[page_number] = l

    def __getitem__(self, index):
        if index > self.page_size * self.max_pages:
            raise IndexError('list index out of range')
        normalized_index = index % self.page_size
        target_page = math.ceil((index+1)/self.page_size)-1

        if not self.lists[target_page]:
            self._load_page(target_page)

        return self.lists[target_page][normalized_index]

    def __len__(self):
        return self.total_items

