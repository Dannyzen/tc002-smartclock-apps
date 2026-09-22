"""Unit tests for Shabbat times tool and Hebcal API parser."""

import unittest
from unittest import mock

from apps.shabbat import get_shabbat_info, push_to_awtrix


class TestShabbatApp(unittest.TestCase):
    def test_get_shabbat_info_parsing(self):
        fake_response = {
            "location": {"title": "New York, NY 10001"},
            "items": [
                {
                    "category": "candles",
                    "title": "Candle lighting: 6:36 PM",
                    "date": "2026-09-25T18:36:00-04:00",
                },
                {
                    "category": "havdalah",
                    "title": "Havdalah: 7:34 PM",
                    "date": "2026-09-26T19:34:00-04:00",
                },
                {
                    "category": "parashat",
                    "title": "Parashat Ha'Azinu",
                },
            ],
        }

        with mock.patch("urllib.request.urlopen"):
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = b""
            mock_resp.__enter__.return_value = mock_resp
            with mock.patch("json.load", return_value=fake_response):
                info = get_shabbat_info(zip_code="10001")
                self.assertEqual(info["candle_time"], "6:36 PM")
                self.assertEqual(info["candle_date"], "2026-09-25T18:36:00-04:00")
                self.assertEqual(info["havdalah_time"], "7:34 PM")
                self.assertEqual(info["parasha"], "Parashat Ha'Azinu")
                self.assertIn("New York", info["location"])

    def test_push_to_awtrix_sets_explicit_duration_when_requested(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        with (
            mock.patch("urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("json.load", return_value={"ok": True}),
        ):
            push_to_awtrix(
                "clock.lan", 8080, "", "", "shabbat", "6:36", duration_ms=7000
            )
        payload = __import__("json").loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["durationMs"], 7000)


if __name__ == "__main__":
    unittest.main()
