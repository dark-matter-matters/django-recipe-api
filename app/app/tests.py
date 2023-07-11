"""
Sample tests
"""

from django.test import SimpleTestCase

from app import calc


class CalcTest(SimpleTestCase):
    """
    Test calc module
    """

    def test_add(self):
        """Test x+y"""
        res = calc.add(5, 6)

        self.assertEqual(res, 11)

    def test_substract(self):
        """Test substracting"""
        res = calc.substract(10, 5)

        self.assertEqual(res, 5)
