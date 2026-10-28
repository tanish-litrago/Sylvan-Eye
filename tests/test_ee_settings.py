"""
Tests for the Earth Engine project setting and its error message (no Earth Engine needed: a fake `ee`
module stands in): python -m tests.test_ee_settings
"""

import importlib
import os
import sys
import types

from phases import phase1_data_pipeline as p1


def fake_ee(fail_with=None):
    calls = []
    mod = types.ModuleType("ee")

    def initialize(project=None):
        calls.append(project)
        if fail_with:
            raise fail_with
    mod.Initialize = initialize
    return mod, calls


def with_fake_ee(mod, fn):
    old = sys.modules.get("ee")
    sys.modules["ee"] = mod
    try:
        return fn()
    finally:
        if old is None:
            sys.modules.pop("ee", None)
        else:
            sys.modules["ee"] = old


def test_project_comes_from_the_environment():
    old = os.environ.get("SYLVAN_EE_PROJECT")
    try:
        os.environ["SYLVAN_EE_PROJECT"] = "my-own-project"
        assert importlib.reload(p1).EE_PROJECT == "my-own-project"
        del os.environ["SYLVAN_EE_PROJECT"]
        assert importlib.reload(p1).EE_PROJECT == "sylvan-eye"      # the author's project is only the fallback
    finally:
        if old is not None:
            os.environ["SYLVAN_EE_PROJECT"] = old
        importlib.reload(p1)


def test_earth_engine_is_started_with_that_project():
    mod, calls = fake_ee()
    with_fake_ee(mod, p1.init_earth_engine)
    assert calls == [p1.EE_PROJECT]


def test_a_failing_start_says_how_to_fix_it():
    for reason in (PermissionError("not allowed"), RuntimeError("Quota exceeded")):
        mod, _ = fake_ee(fail_with=reason)
        try:
            with_fake_ee(mod, p1.init_earth_engine)
        except RuntimeError as e:
            assert "SYLVAN_EE_PROJECT" in str(e) and p1.EE_PROJECT in str(e) and "earthengine authenticate" in str(e)
            assert e.__cause__ is reason          # the original error is kept
        else:
            raise AssertionError("a failing Earth Engine start must raise")


if __name__ == "__main__":
    test_project_comes_from_the_environment()
    test_earth_engine_is_started_with_that_project()
    test_a_failing_start_says_how_to_fix_it()
    print("all ee settings tests passed")
