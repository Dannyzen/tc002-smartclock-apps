"""Unit tests for the Kitchen Clock Time-first app-loop profile."""

import json
import unittest
import urllib.error
from unittest import mock

from apps.configure_time_first import (
    TIME_APP_DURATION_MS,
    build_time_first_plan,
    configure_time_first,
)


class TestTimeFirstCycle(unittest.TestCase):
    def inventory(self):
        return [
            {
                "name": "Time",
                "enabled": True,
                "inLoop": True,
                "slot": 0,
                "present": True,
                "origin": "builtin",
            },
            {
                "name": "Date",
                "enabled": True,
                "inLoop": True,
                "slot": 1,
                "present": True,
                "origin": "builtin",
            },
            {
                "name": "Battery",
                "enabled": True,
                "inLoop": True,
                "slot": 2,
                "present": True,
                "origin": "builtin",
            },
            {
                "name": "shabbat",
                "enabled": True,
                "inLoop": True,
                "slot": 3,
                "present": True,
                "origin": "pushed",
            },
            {
                "name": "sports",
                "enabled": True,
                "inLoop": True,
                "slot": 4,
                "present": True,
                "origin": "pushed",
            },
            {
                "name": "draft",
                "enabled": False,
                "inLoop": False,
                "slot": None,
                "present": True,
                "origin": "pushed",
            },
            {
                "name": "helper",
                "enabled": True,
                "inLoop": True,
                "slot": 5,
                "present": True,
                "origin": "script",
                "headless": True,
            },
        ]

    def test_build_plan_puts_time_then_kitchen_apps_and_disables_other_builtins(self):
        plan = build_time_first_plan(self.inventory())
        self.assertEqual(
            plan["settings"],
            {"autoTransition": True, "appDurationMs": TIME_APP_DURATION_MS},
        )
        self.assertEqual(
            plan["appOrder"]["order"], ["Time", "shabbat", "sports", "helper"]
        )
        self.assertEqual(plan["appOrder"]["disabled"], ["Battery", "Date", "draft"])
        self.assertEqual(plan["visibleKitchenApps"], ["shabbat", "sports"])

    def test_build_plan_requires_time_and_a_visible_kitchen_app(self):
        with self.assertRaisesRegex(ValueError, "Time"):
            build_time_first_plan([])
        with self.assertRaisesRegex(ValueError, "no present pushed or script apps"):
            build_time_first_plan(
                [
                    {
                        "name": "Time",
                        "enabled": True,
                        "present": True,
                        "origin": "builtin",
                    }
                ]
            )

    @mock.patch("json.load")
    @mock.patch("urllib.request.urlopen")
    def test_dry_run_reads_inventory_without_writing(self, urlopen, json_load):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        urlopen.return_value = response
        json_load.return_value = self.inventory()
        plan = configure_time_first("clock.lan", 8080, "", "", apply=False)
        self.assertEqual(plan["appOrder"]["order"][0], "Time")
        self.assertEqual(urlopen.call_count, 1)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "http://clock.lan:8080/api/v1/apps")

    @mock.patch("json.load")
    @mock.patch("urllib.request.urlopen")
    def test_apply_writes_settings_then_app_order(self, urlopen, json_load):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        urlopen.return_value = response
        json_load.side_effect = [
            self.inventory(),
            {"autoTransition": False, "appDurationMs": 7000},
            {"ok": True},
            {"ok": True},
        ]
        configure_time_first("clock.lan", 8080, "", "", apply=True)
        self.assertEqual(urlopen.call_count, 4)
        prior_settings_request = urlopen.call_args_list[1].args[0]
        settings_request = urlopen.call_args_list[2].args[0]
        order_request = urlopen.call_args_list[3].args[0]
        self.assertEqual(prior_settings_request.get_method(), "GET")
        self.assertEqual(
            prior_settings_request.full_url, "http://clock.lan:8080/api/v1/settings"
        )
        self.assertEqual(settings_request.get_method(), "PATCH")
        self.assertEqual(
            settings_request.full_url, "http://clock.lan:8080/api/v1/settings"
        )
        self.assertEqual(
            json.loads(settings_request.data),
            {"autoTransition": True, "appDurationMs": TIME_APP_DURATION_MS},
        )
        self.assertEqual(order_request.get_method(), "PUT")
        self.assertEqual(
            order_request.full_url, "http://clock.lan:8080/api/v1/apps/order"
        )
        self.assertEqual(
            json.loads(order_request.data),
            {
                "order": ["Time", "shabbat", "sports", "helper"],
                "disabled": ["Battery", "Date", "draft"],
            },
        )

    @mock.patch("apps.configure_time_first.request_json")
    def test_order_failure_restores_previous_settings(self, request_json):
        previous_settings = {"autoTransition": False, "appDurationMs": 7000}
        request_json.side_effect = [
            self.inventory(),
            previous_settings,
            {"ok": True},
            urllib.error.URLError("order write failed"),
            {"ok": True},
        ]
        with self.assertRaisesRegex(OSError, "order write failed"):
            configure_time_first("clock.lan", 8080, "", "", apply=True)
        self.assertEqual(request_json.call_count, 5)
        rollback_call = request_json.call_args_list[-1]
        self.assertEqual(rollback_call.args[4], "/api/v1/settings")
        self.assertEqual(rollback_call.kwargs["method"], "PATCH")
        self.assertEqual(rollback_call.kwargs["payload"], previous_settings)


if __name__ == "__main__":
    unittest.main()
