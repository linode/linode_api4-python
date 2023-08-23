from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import BetaProgram


class BetaProgramTest(ClientBaseCase):
    """
    Test the methods of the Beta Program.
    """

    def test_beta_program_api_get(self):
        beta_id = "active"
        beta_program_api_get_url = "/betas/{}".format(beta_id)

        with self.mock_get(beta_program_api_get_url) as m:
            beta_program = BetaProgram(self.client, beta_id)
            self.assertEqual(beta_program.id, beta_id)
            self.assertEqual(beta_program.label, "active closed beta")
            self.assertEqual(beta_program.description, "An active closed beta")
            self.assertEqual(
                beta_program.started, datetime(2018, 1, 2, 3, 4, 5)
            )
            self.assertEqual(beta_program.ended, None)
            self.assertEqual(beta_program.greenlight_only, True)
            self.assertEqual(
                beta_program.more_info, "a link with even more info"
            )

            self.assertEqual(m.call_url, beta_program_api_get_url)
