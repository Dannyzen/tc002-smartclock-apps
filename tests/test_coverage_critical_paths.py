"""Behavior coverage for birthday and Time-first safety-critical CLI paths."""

import base64
import contextlib
import datetime
import io
import json
import os
import runpy
import sys
import unittest
from unittest import mock

from apps import birthdays, configure_time_first, install_birthday_scripts


class TestBirthdayCriticalPaths(unittest.TestCase):
    def _load_birthdays_with_env(self, value):
        with mock.patch.dict(os.environ, {"BIRTHDAYS_JSON_B64": value}, clear=False):
            return birthdays.load_birthdays()

    def test_load_birthdays_uses_runtime_secret_and_fails_closed(self):
        encoded = base64.b64encode(b'[{"name":"Test","month":1,"day":2}]').decode()
        self.assertEqual(self._load_birthdays_with_env(encoded)[0]["name"], "Test")
        with self.assertRaisesRegex(ValueError, "base64 JSON"):
            self._load_birthdays_with_env("%%%")
        with self.assertRaisesRegex(TypeError, "JSON array"):
            self._load_birthdays_with_env(base64.b64encode(b"{}").decode())
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(ValueError, "required"),
        ):
            birthdays.load_birthdays()

    def test_load_birthdays_uses_environment_runtime_secret(self):
        encoded = base64.b64encode(b'[{"name":"Test","month":1,"day":2}]').decode()
        self.assertEqual(self._load_birthdays_with_env(encoded)[0]["name"], "Test")

    def test_calculate_days_until_uses_today_when_not_supplied(self):
        class FixedDate(datetime.date):
            @classmethod
            def today(cls):
                return cls(2026, 1, 1)

        with mock.patch("apps.birthdays.datetime.date", FixedDate):
            days, target = birthdays.calculate_days_until(1, 2)
        self.assertEqual((days, target), (1, datetime.date(2026, 1, 2)))

    def test_push_to_awtrix_auth_icon_duration_and_response(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("json.load", return_value={"ok": True}),
        ):
            result = birthdays.push_to_awtrix(
                "clock.lan",
                8080,
                "user",
                "password",
                "ada",
                "Ada",
                icon="cake",
                duration_ms=3000,
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(result, {"ok": True})
        self.assertEqual(
            request.get_header("Authorization"), "Basic dXNlcjpwYXNzd29yZA=="
        )
        self.assertEqual(json.loads(request.data)["icon"], "cake")
        self.assertEqual(json.loads(request.data)["durationMs"], 3000)

    def test_push_to_awtrix_omits_optional_fields_without_auth(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("json.load", return_value={"ok": True}),
        ):
            birthdays.push_to_awtrix("clock.lan", 8080, "", "", "ada", "Ada")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertIsNone(request.get_header("Authorization"))
        self.assertNotIn("icon", payload)
        self.assertNotIn("durationMs", payload)

    def test_birthday_module_entrypoint_executes_with_mocked_clock(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response),
            mock.patch("json.load", return_value={"ok": True}),
            mock.patch.dict(
                os.environ,
                {"BIRTHDAYS_JSON_B64": base64.b64encode(b"[]").decode()},
                clear=False,
            ),
            mock.patch.object(sys, "argv", ["birthdays.py"]),
        ):
            runpy.run_module("apps.birthdays", run_name="__main__")

    @mock.patch("apps.birthdays.push_to_awtrix")
    @mock.patch("apps.birthdays.calculate_days_until")
    @mock.patch("apps.birthdays.load_birthdays")
    @mock.patch("sys.argv", ["birthdays.py", "--host", "clock.lan"])
    def test_main_renders_today_one_day_and_plural_and_continues_after_failure(
        self, load_birthdays, calculate_days_until, push_to_awtrix
    ):
        load_birthdays.return_value = [
            {"name": "Today", "month": 1, "day": 1},
            {"name": "One", "month": 1, "day": 2},
            {"name": "Many", "month": 1, "day": 3},
            {"name": "Broken", "month": 1, "day": 4},
        ]
        calculate_days_until.side_effect = [
            (0, datetime.date(2026, 1, 1)),
            (1, datetime.date(2026, 1, 2)),
            (2, datetime.date(2026, 1, 3)),
            (3, datetime.date(2026, 1, 4)),
        ]
        push_to_awtrix.side_effect = [
            None,
            None,
            None,
            None,
            None,
            None,
            OSError("offline"),
        ]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            birthdays.main()
        calls = push_to_awtrix.call_args_list
        self.assertEqual(len(calls), 7)
        self.assertEqual(calls[1].kwargs["text"], "TODAY!")
        self.assertEqual(calls[3].kwargs["text"], "1 Day")
        self.assertEqual(calls[5].kwargs["text"], "2 Days")
        self.assertIn("Failed pushing birthday", stderr.getvalue())

    @mock.patch("apps.birthdays.time.sleep", side_effect=StopIteration)
    @mock.patch("apps.birthdays.push_to_awtrix")
    @mock.patch(
        "apps.birthdays.calculate_days_until",
        return_value=(2, datetime.date(2026, 1, 3)),
    )
    @mock.patch(
        "apps.birthdays.load_birthdays",
        return_value=[{"name": "Ada", "month": 1, "day": 3}],
    )
    @mock.patch("sys.argv", ["birthdays.py", "--daemon"])
    def test_daemon_sleeps_after_daily_run(self, _load, _calculate, _push, sleep):
        with self.assertRaises(StopIteration):
            birthdays.main()
        sleep.assert_called_once_with(86400)


class TestTimeFirstCriticalPaths(unittest.TestCase):
    def test_request_json_auth_payload_and_response(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("json.load", return_value={"ok": True}),
        ):
            result = configure_time_first.request_json(
                "clock.lan",
                8080,
                "user",
                "password",
                "/api/v1/settings",
                method="PATCH",
                payload={"x": 1},
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(result, {"ok": True})
        self.assertEqual(
            request.get_header("Authorization"), "Basic dXNlcjpwYXNzd29yZA=="
        )
        self.assertEqual(json.loads(request.data), {"x": 1})

    def test_time_first_module_entrypoint_executes_dry_run(self):
        inventory = [
            {
                "name": "Time",
                "enabled": True,
                "present": True,
                "origin": "builtin",
                "slot": 0,
            },
            {
                "name": "birthday-ada",
                "enabled": True,
                "present": True,
                "origin": "script",
                "slot": 1,
            },
        ]
        response = mock.MagicMock()
        response.__enter__.return_value = response
        stdout = io.StringIO()
        with (
            mock.patch("urllib.request.urlopen", return_value=response),
            mock.patch("json.load", return_value=inventory),
            mock.patch.object(
                sys, "argv", ["configure_time_first.py", "--host", "clock.lan"]
            ),
            contextlib.redirect_stdout(stdout),
        ):
            runpy.run_module("apps.configure_time_first", run_name="__main__")
        self.assertTrue(json.loads(stdout.getvalue())["applied"] is False)

    @mock.patch("apps.configure_time_first.request_json")
    def test_rollback_failure_is_explicit(self, request_json):
        inventory = [
            {
                "name": "Time",
                "enabled": True,
                "present": True,
                "origin": "builtin",
                "slot": 0,
            },
            {
                "name": "birthday-ada",
                "enabled": True,
                "present": True,
                "origin": "script",
                "slot": 1,
            },
        ]
        request_json.side_effect = [
            inventory,
            {"autoTransition": False, "appDurationMs": 7000},
            {"ok": True},
            OSError("order failed"),
            OSError("rollback failed"),
        ]
        with self.assertRaisesRegex(RuntimeError, "rollback failed"):
            configure_time_first.configure_time_first(
                "clock.lan", 8080, "", "", apply=True
            )


class TestInstallerCriticalPaths(unittest.TestCase):
    def _load_installer_birthdays_with_env(self, value):
        with mock.patch.dict(
            os.environ, {"BIRTHDAYS_JSON_B64": value or ""}, clear=False
        ):
            return install_birthday_scripts.load_birthdays()

    def test_script_name_and_validation_rejections(self):
        for value in ("", "!!!"):
            with self.assertRaises(ValueError):
                install_birthday_scripts.script_name(value)
        with self.assertRaises(ValueError):
            install_birthday_scripts.script_name("a" * 40)
        for payload, expected in (
            ({}, ValueError),
            ({"name": "", "month": 1, "day": 1}, ValueError),
            ({"name": "Ada", "month": "1", "day": 1}, TypeError),
            ({"name": "Ada", "month": 4, "day": 31}, ValueError),
            ({"name": "Ada", "month": 1, "day": 1, "leap_day": "never"}, ValueError),
            ({"name": "Ada", "month": 1, "day": 1, "color": "blue"}, ValueError),
        ):
            with self.assertRaises(expected):
                install_birthday_scripts.validate_birthday(payload)

    def test_runtime_payload_rejects_empty_invalid_and_non_array_data(self):
        for value in (
            None,
            "",
            "%%%",
            base64.b64encode(b"[]").decode(),
            base64.b64encode(b"{}").decode(),
        ):
            with self.assertRaises(ValueError):
                self._load_installer_birthdays_with_env(value)

    def test_runtime_payload_accepts_valid_data_and_installer_entrypoint_dry_runs(self):
        encoded = base64.b64encode(b'[{"name":"Test","month":1,"day":2}]').decode()
        self.assertEqual(
            self._load_installer_birthdays_with_env(encoded)[0]["name"], "Test"
        )
        stdout = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"BIRTHDAYS_JSON_B64": encoded}, clear=False),
            mock.patch.object(
                sys,
                "argv",
                ["install_birthday_scripts.py", "--host", "clock.lan"],
            ),
            contextlib.redirect_stdout(stdout),
        ):
            runpy.run_module("apps.install_birthday_scripts", run_name="__main__")
        self.assertFalse(json.loads(stdout.getvalue())["applied"])

    def test_plan_rejects_normalized_name_collision(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            install_birthday_scripts.build_install_plan(
                [
                    {"name": "A B", "month": 1, "day": 1},
                    {"name": "A-B", "month": 1, "day": 2},
                ]
            )

    def test_request_adds_auth_and_content_type(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("json.load", return_value={"ok": True}),
        ):
            install_birthday_scripts.request(
                "clock.lan",
                8080,
                "user",
                "password",
                "/test",
                method="PUT",
                body=b"x",
                content_type="text/plain",
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.get_header("Authorization"), "Basic dXNlcjpwYXNzd29yZA=="
        )
        self.assertEqual(request.get_header("Content-type"), "text/plain")


if __name__ == "__main__":
    unittest.main()
