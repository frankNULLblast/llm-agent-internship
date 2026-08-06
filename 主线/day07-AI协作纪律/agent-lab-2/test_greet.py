import unittest

from greet import greet


class GreetTests(unittest.TestCase):
    def test_name(self) -> None:
        self.assertEqual(greet("Lin"), "Hello, Lin!")

    def test_blank_raises(self) -> None:
        with self.assertRaises(ValueError):
            greet("   ")


if __name__ == "__main__":
    unittest.main()
