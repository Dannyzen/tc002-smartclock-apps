"""Static contract tests for the persistent AWTRIX NG birthday script."""

import json
import unittest
from pathlib import Path
from unittest import mock

from apps.install_birthday_scripts import (
    build_install_plan,
    install_birthdays,
    validate_birthday,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "birthday_countdown.be"


class TestBirthdayScript(unittest.TestCase):
    def test_script_uses_on_clock_calendar_loop_and_dwell(self):
        source = SCRIPT.read_text()
        for token in (
            "def loop()",
            "year()",
            "month()",
            "day()",
            "def duration()",
            'store.get("leapDay")',
            "default=feb28 options=feb28,mar1",
            "return BirthdayCountdown()",
        ):
            self.assertIn(token, source)

    def test_script_checks_february_29_policy_before_generic_day_validation(self):
        source = SCRIPT.read_text()
        policy = source.index("if target_month == 2 && target_day == 29")
        generic_guard = source.index("if target_day > self.days_in_month")
        self.assertLess(policy, generic_guard)

    def test_install_plan_uses_persistent_per_person_script_config(self):
        plan = build_install_plan(
            [{"name": "Zach", "month": 2, "day": 29, "color": "#00e5ff"}]
        )
        self.assertEqual(plan[0]["script"], "birthday-zach")
        self.assertEqual(plan[0]["config"]["leapDay"], "feb28")
        self.assertEqual(plan[0]["config"]["color"], "#00E5FF")

    def test_person_field_limit_and_awtrix_error_response_are_rejected(self):
        self.assertEqual(
            validate_birthday({"name": "x" * 18, "month": 1, "day": 1})["name"],
            "x" * 18,
        )
        with self.assertRaisesRegex(ValueError, "18 characters"):
            validate_birthday({"name": "x" * 19, "month": 1, "day": 1})
        with (
            mock.patch(
                "apps.install_birthday_scripts.request",
                return_value={"ok": True, "error": "compile failed"},
            ),
            self.assertRaisesRegex(RuntimeError, "compile failed"),
        ):
            install_birthdays(
                "clock.lan",
                8080,
                "",
                "",
                [{"name": "Ada", "month": 1, "day": 1}],
                apply=True,
            )

    @mock.patch("apps.install_birthday_scripts.request")
    def test_apply_rejects_missing_script_in_inventory_readback(self, request):
        request.side_effect = [
            {"ok": True, "error": None},
            {"ok": True, "error": None},
            [],
        ]
        with self.assertRaisesRegex(RuntimeError, "readback is missing birthday-ada"):
            install_birthdays(
                "clock.lan",
                8080,
                "",
                "",
                [{"name": "Ada", "month": 1, "day": 1}],
                apply=True,
            )

    def test_invalid_calendar_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid birthday"):
            validate_birthday({"name": "Invalid", "month": 4, "day": 31})

    def test_dry_run_does_not_open_network(self):
        birthday = validate_birthday({"name": "Dad", "month": 10, "day": 12})
        plan = install_birthdays("clock.lan", 8080, "", "", [birthday], apply=False)
        self.assertEqual(json.loads(json.dumps(plan))[0]["script"], "birthday-dad")

    @mock.patch("json.load")
    @mock.patch("urllib.request.urlopen")
    def test_apply_uploads_source_then_persists_person_config(self, urlopen, json_load):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        urlopen.return_value = response
        json_load.side_effect = [
            {"ok": True, "error": None},
            {"ok": True, "error": None},
            [{"name": "birthday-zach", "origin": "script", "present": True}],
        ]
        birthday = validate_birthday(
            {"name": "Zach", "month": 2, "day": 29, "color": "#00E5FF"}
        )
        install_birthdays("clock.lan", 8080, "", "", [birthday], apply=True)
        self.assertEqual(urlopen.call_count, 3)
        source_request = urlopen.call_args_list[0].args[0]
        config_request = urlopen.call_args_list[1].args[0]
        inventory_request = urlopen.call_args_list[2].args[0]
        self.assertEqual(source_request.get_method(), "PUT")
        self.assertEqual(
            source_request.full_url,
            "http://clock.lan:8080/api/v1/apps/script/birthday-zach",
        )
        self.assertEqual(source_request.get_header("Content-type"), "text/plain")
        self.assertEqual(source_request.data, SCRIPT.read_bytes())
        self.assertEqual(config_request.get_method(), "PATCH")
        self.assertEqual(
            config_request.full_url,
            "http://clock.lan:8080/api/v1/apps/birthday-zach/config",
        )
        self.assertEqual(inventory_request.get_method(), "GET")
        self.assertEqual(
            inventory_request.full_url, "http://clock.lan:8080/api/v1/apps"
        )
        self.assertEqual(
            json.loads(config_request.data),
            {
                "person": "Zach",
                "birthMonth": 2,
                "birthDay": 29,
                "color": "#00E5FF",
                "leapDay": "feb28",
                "dwellMs": 6000,
            },
        )


if __name__ == "__main__":
    unittest.main()
