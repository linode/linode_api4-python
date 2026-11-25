from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linode_api4.linode_client import BaseClient


class Group:
    def __init__(self, client: BaseClient):
        self.client = client
