"""Unit tests for Birthday countdown calculator and flip card generator."""

import datetime
import unittest

from apps.birthdays import birthday_date_for_year, calculate_days_until


class TestBirthdaysApp(unittest.TestCase):
    def test_calculate_days_until_future(self):
        today = datetime.date(2026, 9, 20)

        # Person 1 (Oct 12) -> 22 days
        days_1, target_1 = calculate_days_until(10, 12, now=today)
        self.assertEqual(days_1, 22)
        self.assertEqual(target_1, datetime.date(2026, 10, 12))

        # Person 2 (Nov 25) -> 66 days
        days_2, target_2 = calculate_days_until(11, 25, now=today)
        self.assertEqual(days_2, 66)
        self.assertEqual(target_2, datetime.date(2026, 11, 25))

        # Person 3 (Dec 26) -> 97 days
        days_3, target_3 = calculate_days_until(12, 26, now=today)
        self.assertEqual(days_3, 97)
        self.assertEqual(target_3, datetime.date(2026, 12, 26))

    def test_calculate_days_until_same_day(self):
        today = datetime.date(2026, 10, 12)
        days, target = calculate_days_until(10, 12, now=today)
        self.assertEqual(days, 0)
        self.assertEqual(target, today)

    def test_february_29_defaults_to_february_28_in_non_leap_years(self):
        before = datetime.date(2026, 2, 27)
        days, target = calculate_days_until(2, 29, now=before)
        self.assertEqual(days, 1)
        self.assertEqual(target, datetime.date(2026, 2, 28))
        after = datetime.date(2026, 3, 1)
        days, target = calculate_days_until(2, 29, now=after)
        self.assertEqual(target, datetime.date(2027, 2, 28))
        self.assertEqual(days, (target - after).days)

    def test_february_29_can_use_march_1_policy(self):
        self.assertEqual(
            birthday_date_for_year(2, 29, 2026, "mar1"), datetime.date(2026, 3, 1)
        )
        self.assertEqual(
            birthday_date_for_year(2, 29, 2028, "feb28"), datetime.date(2028, 2, 29)
        )

    def test_calculate_days_until_past_wraps_to_next_year(self):
        today = datetime.date(2026, 10, 13)
        days, target = calculate_days_until(10, 12, now=today)
        self.assertEqual(days, 364)
        self.assertEqual(target, datetime.date(2027, 10, 12))


if __name__ == "__main__":
    unittest.main()
