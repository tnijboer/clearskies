import unittest
from unittest.mock import MagicMock, call
from .model import Model
from .columns import Columns
from .column_types import String, Integer
from .input_requirements import Required, MinimumLength, MaximumLength, maximum_length
from .di import StandardDependencies


class ColumnsTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.columns = Columns(self.di)

    def test_configure(self):
        columns = self.columns.configure(
            {
                "first_name": {
                    "class": String,
                    "input_requirements": [Required, (MinimumLength, 2), maximum_length(15)],
                },
                "last_name": {
                    "class": String,
                    "input_requirements": [Required],
                },
                "age": {
                    "class": Integer,
                },
            },
            Model,
        )

        self.assertEqual(3, len(columns))
        self.assertTrue("first_name" in columns)
        self.assertTrue("last_name" in columns)
        self.assertTrue("age" in columns)
        self.assertEqual("first_name", columns["first_name"].name)
        self.assertEqual("last_name", columns["last_name"].name)
        self.assertEqual("age", columns["age"].name)
        self.assertEqual(3, len(columns["first_name"].config("input_requirements")))
        self.assertEqual(1, len(columns["last_name"].config("input_requirements")))
        self.assertEqual(0, len(columns["age"].config("input_requirements")))

        self.assertEqual(Required, columns["last_name"].config("input_requirements")[0].__class__)
        first_name_requirements = columns["first_name"].config("input_requirements")
        self.assertEqual(Required, first_name_requirements[0].__class__)
        self.assertEqual(MinimumLength, first_name_requirements[1].__class__)
        self.assertEqual(MaximumLength, first_name_requirements[2].__class__)
        self.assertEqual(2, first_name_requirements[1].minimum_length)
        self.assertEqual(15, first_name_requirements[2].maximum_length)

    def test_overrides(self):
        columns = self.columns.configure(
            {
                "first_name": {
                    "class": String,
                    "input_requirements": [Required, (MinimumLength, 2), maximum_length(15)],
                },
                "last_name": {
                    "class": String,
                    "input_requirements": [Required],
                },
            },
            Model,
            overrides={
                "age": {"class": Integer, "input_requirements": [Required]},
                "first_name": {"input_requirements": [maximum_length(5)]},
                "last_name": {"input_requirements": [maximum_length(25)]},
            },
        )

        self.assertEqual(3, len(columns))
        self.assertTrue("first_name" in columns)
        self.assertTrue("last_name" in columns)
        self.assertTrue("age" in columns)
        self.assertEqual("first_name", columns["first_name"].name)
        self.assertEqual("last_name", columns["last_name"].name)
        self.assertEqual("age", columns["age"].name)
        self.assertEqual(3, len(columns["first_name"].config("input_requirements")))
        self.assertEqual(2, len(columns["last_name"].config("input_requirements")))
        self.assertEqual(1, len(columns["age"].config("input_requirements")))

        self.assertEqual(MaximumLength, columns["last_name"].config("input_requirements")[0].__class__)
        self.assertEqual(Required, columns["last_name"].config("input_requirements")[1].__class__)
        first_name_requirements = columns["first_name"].config("input_requirements")
        last_name_requirements = columns["last_name"].config("input_requirements")
        self.assertEqual(MaximumLength, first_name_requirements[0].__class__)
        self.assertEqual(Required, first_name_requirements[1].__class__)
        self.assertEqual(MinimumLength, first_name_requirements[2].__class__)
        self.assertEqual(5, first_name_requirements[0].maximum_length)
        self.assertEqual(2, first_name_requirements[2].minimum_length)
        self.assertEqual(25, last_name_requirements[0].maximum_length)
