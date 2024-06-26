from .public import Public
import unittest
from unittest.mock import MagicMock


class PublicTest(unittest.TestCase):
    def test_headers(self):
        public = Public()
        self.assertEqual({}, public.headers())

    def test_good_auth(self):
        self.assertTrue(Public().authenticate(None))
