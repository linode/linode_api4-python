import json
import os
import re
import sys

# Determine fixtures directory relative to this file to avoid relying on sys.path[0]
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")

# This regex is useful for finding individual underscore characters,
# which is necessary to allow us to use underscores in URL paths.
PATH_REPLACEMENT_REGEX = re.compile(r"(?<!_)_(?!_)")


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
        # If the fixture isn't found, attempt to reload fixtures. This is
        # helpful in test runs where fixtures may be added after the
        # TestFixtures singleton was constructed.
        if url not in self.fixtures:
            self._load_fixtures()

        return self.fixtures[url]

    def _load_fixtures(self):
        """
        Handles loading JSON files and parsing them into responses.  Also splits
        returned lists into individual models that may be returned on their own.
        """
        self.fixtures = {}

        for json_file in os.listdir(FIXTURES_DIR):
            if not json_file.endswith(".json"):
                continue

            with open(FIXTURES_DIR + "/" + json_file) as f:
                raw = f.read()

            data = json.loads(raw)

            fixture_url = PATH_REPLACEMENT_REGEX.sub("/", json_file).replace(
                "__", "_"
            )[:-5]

            self.fixtures[fixture_url] = data

            if "results" in data:
                # this is a paginated response
                for obj in data["data"]:
                    if "id" in obj:  # tags, obj-buckets don't have ids
                        self.fixtures[fixture_url + "/" + str(obj["id"])] = obj
