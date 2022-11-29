from unittest import TestCase

from linode_api4 import OAuthScopes


class OAuthScopesTest(TestCase):
    def test_parse_scopes_none(self):
        """
        Tests parsing no scopes
        """
        scopes = OAuthScopes.parse("")
        self.assertEqual(scopes, [])

    def test_parse_scopes_single(self):
        """
        Tests parsing a single scope
        """
        scopes = OAuthScopes.parse("linodes:read_only")
        self.assertEqual(scopes, [OAuthScopes.Linodes.read_only])

    def test_parse_scopes_many(self):
        """
        Tests parsing many scopes
        """
        scopes = OAuthScopes.parse("linodes:read_only domains:read_write")
        self.assertEqual(scopes, [OAuthScopes.Linodes.read_only, OAuthScopes.Domains.read_write])
        
    def test_parse_scopes_all(self):
        """
        Tests parsing * scopes
        """
        scopes = OAuthScopes.parse("*")
        self.assertEqual(scopes, [getattr(c, "all") for c in OAuthScopes._scope_families.values()])
