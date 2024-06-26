import unittest
from unittest.mock import MagicMock
from .maximum_length import MaximumLength


class MaximumLengthTest(unittest.TestCase):
    def setUp(self):
        self.maximum_length = MaximumLength()
        self.maximum_length.column_name = "name"

    def test_check_length(self):
        self.maximum_length.configure(10)

        error = self.maximum_length.check("model", {"name": "1234567890"})
        self.assertEqual("", error)
        error = self.maximum_length.check("model", {"name": ""})
        self.assertEqual("", error)
        error = self.maximum_length.check("model", {})
        self.assertEqual("", error)
        error = self.maximum_length.check("model", {"name": "123456789"})
        self.assertEqual("", error)
        error = self.maximum_length.check("model", {"name": "12345678901"})
        self.assertEqual("'name' must be at most 10 characters long.", error)

    def test_check_configuration_length_not_int(self):
        with self.assertRaises(ValueError) as context:
            self.maximum_length.configure("asdf")
        self.assertEqual(
            "Maximum length must be an int to use the MaximumLength class for column 'name'", str(context.exception)
        )
