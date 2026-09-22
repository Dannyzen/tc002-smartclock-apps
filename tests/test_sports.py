"""Unit tests for ESPN sports scores parser and compact text formatter."""

import unittest
from unittest import mock

from apps.sports import FINAL_SCORE_DURATION_MS, format_compact_time, get_games, main


class TestSportsApp(unittest.TestCase):
    def test_format_compact_time(self):
        self.assertEqual(format_compact_time("10/5 - 7:00 PM EDT"), "10/5 7P")
        self.assertEqual(format_compact_time("Sun, 1:00 PM EST"), "Sun, 1P")
        self.assertEqual(format_compact_time("7:00 PM"), "7P")
        self.assertEqual(format_compact_time("Final"), "Final")

    @mock.patch("apps.sports.push_to_awtrix")
    @mock.patch("apps.sports.get_games")
    @mock.patch("sys.argv", ["sports.py", "--sport", "nba"])
    def test_final_game_uses_explicit_short_duration(self, get_games, push_to_awtrix):
        get_games.return_value = [
            {
                "sport": "NBA",
                "state": "post",
                "away": "NY",
                "home": "PHI",
                "away_score": "110",
                "home_score": "102",
            }
        ]
        main()
        self.assertEqual(push_to_awtrix.call_count, 1)
        self.assertEqual(
            push_to_awtrix.call_args.kwargs["duration_ms"], FINAL_SCORE_DURATION_MS
        )

    def test_get_games_parsing_nba(self):
        fake_espn_data = {
            "events": [
                {
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {"abbreviation": "PHI"},
                                    "score": "85",
                                },
                                {
                                    "homeAway": "away",
                                    "team": {"abbreviation": "NY"},
                                    "score": "88",
                                },
                            ],
                            "status": {
                                "type": {"state": "in", "shortDetail": "Q4 2:15"},
                                "displayClock": "2:15",
                                "period": 4,
                            },
                        }
                    ]
                }
            ]
        }

        with mock.patch("urllib.request.urlopen"):
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = b""
            mock_resp.__enter__.return_value = mock_resp
            with mock.patch("json.load", return_value=fake_espn_data):
                games = get_games(sport="nba", team_filter="NY")
                self.assertEqual(len(games), 1)
                game = games[0]
                self.assertEqual(game["away"], "NY")
                self.assertEqual(game["home"], "PHI")
                self.assertEqual(game["away_score"], "88")
                self.assertEqual(game["home_score"], "85")
                self.assertEqual(game["state"], "in")
                self.assertEqual(game["period"], 4)


if __name__ == "__main__":
    unittest.main()
