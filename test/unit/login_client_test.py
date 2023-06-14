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
        self.assertEqual(
            scopes,
            [OAuthScopes.Linodes.read_only, OAuthScopes.Domains.read_write],
        )

    def test_parse_scopes_many_comma_delimited(self):
        """
        Tests parsing many scopes that are comma-delimited (which preserves old behavior)
        """
        scopes = OAuthScopes.parse(
            "nodebalancers:read_write,stackscripts:*,events:read_only"
        )
        self.assertEqual(
            scopes,
            [
                OAuthScopes.NodeBalancers.read_write,
                OAuthScopes.StackScripts.all,
                OAuthScopes.Events.read_only,
            ],
        )

    def test_parse_scopes_all(self):
        """
        Tests parsing * scopes
        """
        scopes = OAuthScopes.parse("*")
        self.assertEqual(
            scopes,
            [getattr(c, "all") for c in OAuthScopes._scope_families.values()],
        )
