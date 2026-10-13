import unittest

from tools import calculate_study_time


class CalculatorTests(unittest.TestCase):
    def test_study_time(self):
        self.assertEqual(calculate_study_time(90, 5), {
            "total_minutes": 450, "total_hours": 7.5,
        })

    def test_fractional_hours_are_preserved(self):
        self.assertEqual(calculate_study_time(1, 1)["total_hours"], 1 / 60)

    def test_invalid_values_are_rejected(self):
        for value in (0, -1, True, "90", 1.5, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    calculate_study_time(value, 5)
                with self.assertRaises(ValueError):
                    calculate_study_time(90, value)

    def test_unrealistic_limits_are_rejected(self):
        for minutes, days in ((1441, 1), (90, 367)):
            with self.assertRaises(ValueError):
                calculate_study_time(minutes, days)


if __name__ == "__main__":
    unittest.main()
