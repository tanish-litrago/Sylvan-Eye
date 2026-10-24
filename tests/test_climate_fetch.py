"""
Tests for the Open-Meteo request in phase4_inputs.fetch_daily, with a fake network:  python -m tests.test_climate_fetch
"""

import requests

from phases import phase4_inputs as p4


class Reply:
    def __init__(self, status, body=None, bad_json=False):
        self.status_code, self._body, self._bad_json = status, body, bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


def fetch_with(reply):
    real = requests.get
    requests.get = lambda *a, **k: reply
    try:
        return p4.fetch_daily(20.0, 80.0, 2015, 2024)
    finally:
        requests.get = real


def test_normal_answer_is_returned_as_three_lists():
    body = {"daily": {"time": ["2015-01-01"], "temperature_2m_mean": [20.5], "precipitation_sum": [0.0]}}
    assert fetch_with(Reply(200, body)) == (["2015-01-01"], [20.5], [0.0])


def test_429_names_the_limit_that_was_hit():
    try:
        fetch_with(Reply(429, {"error": True, "reason": "Hourly API request limit exceeded. Please try again in the next hour."}))
        raise AssertionError("should have raised")
    except p4.RateLimited as e:
        assert "Hourly API request limit exceeded" in str(e) and "cached" in str(e)
        assert isinstance(e, RuntimeError)


def test_429_without_a_reason_still_gives_a_clear_message():
    try:
        fetch_with(Reply(429, bad_json=True))
        raise AssertionError("should have raised")
    except p4.RateLimited as e:
        assert "too many requests" in str(e) and "()" not in str(e)


def test_other_errors_are_not_mistaken_for_a_rate_limit():
    try:
        fetch_with(Reply(500))
        raise AssertionError("should have raised")
    except requests.HTTPError:
        pass
    except p4.RateLimited:
        raise AssertionError("a 500 is not a rate limit")


if __name__ == "__main__":
    test_normal_answer_is_returned_as_three_lists()
    test_429_names_the_limit_that_was_hit()
    test_429_without_a_reason_still_gives_a_clear_message()
    test_other_errors_are_not_mistaken_for_a_rate_limit()
    print("all climate fetch tests passed")
