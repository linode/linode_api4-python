import datetime
from unittest import TestCase
from unittest.mock import patch

from linode_api4.polling import TimeoutContext


class TimeoutContextTest(TestCase):
    def test_start_restarts_an_expired_timeout(self):
        started_at = datetime.datetime(2026, 1, 1)
        with patch(
            "linode_api4.polling.datetime.datetime", wraps=datetime.datetime
        ) as clock:
            clock.now.return_value = started_at
            context = TimeoutContext(timeout_seconds=10)
            context.start(started_at)

            for elapsed in (30, 60):
                clock.now.return_value = started_at + datetime.timedelta(
                    seconds=elapsed
                )
                self.assertTrue(context.expired)
                context.start()
                self.assertEqual(context.seconds_remaining, 10)
                self.assertTrue(context.valid)

    def test_start_preserves_explicit_start_time(self):
        started_at = datetime.datetime(2026, 1, 1)
        now = started_at + datetime.timedelta(seconds=7)
        with patch(
            "linode_api4.polling.datetime.datetime", wraps=datetime.datetime
        ) as clock:
            clock.now.return_value = now
            context = TimeoutContext(timeout_seconds=10)
            context.start(started_at)
            self.assertEqual(context.seconds_remaining, 3)
            self.assertTrue(context.valid)
