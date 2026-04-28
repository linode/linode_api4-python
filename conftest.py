import os
import sys

# Ensure the repo root is on sys.path so that `from test.unit.base import ...`
# works regardless of which directory pytest is invoked from.
sys.path.insert(0, os.path.dirname(__file__))
