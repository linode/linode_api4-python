import json
import os
import sys

FIXTURES_DIR = sys.path[0] + '/test/fixtures'

class TestFixtures:
    def __init__(self):
        """
        Creates and loads test fixtures
        """
        self._load_fixtures()

    def get_fixture(self, url):
        """
        Returns the test fixture data loaded at the given URL
        """
        return self.fixtures[url]
    
    def _load_fixtures(self):
        """
        Handles loading JSON files and parsing them into responses.  Also splits
        returned lists into individual models that may be returned on their own.
        """
        self.fixtures = {}

        for json_file in os.listdir(FIXTURES_DIR):
            if not json_file.endswith('.json'):
                continue

            with open(FIXTURES_DIR + '/' + json_file) as f:
                raw = f.read()

            data = json.loads(raw)

            fixture_url = json_file.replace('_', '/')[:-5]
            
            self.fixtures[fixture_url] = data

            if 'results' in data:
                # this is a paginated response
                for obj in data['data']:
                    if 'id' in obj: # tags don't have ids
                        self.fixtures[fixture_url + '/' + str(obj['id'])] = obj
