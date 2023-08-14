from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linode_api4 import LinodeClient


class Group:
    def __init__(self, client: LinodeClient):
        self.client = client
