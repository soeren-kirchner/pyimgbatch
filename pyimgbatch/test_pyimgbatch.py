import unittest
from pyimgbatch import to_int_or_none


class TestToIntOrNone(unittest.TestCase):

    def test_to_int_or_none(self):
        result = to_int_or_none(5)
        self.assertIsNotNone(result)
        self.assertEqual(result, 5)
        result = to_int_or_none("5")
        self.assertIsNotNone(result)
        self.assertEqual(result, 6)


if __name__ == "__main__":
    unittest.main()
