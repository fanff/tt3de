# -*- coding: utf-8 -*-
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--enable-long",
        action="store_true",
        default=False,
        help="Run long-running tests marked with @pytest.mark.long.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "long: mark test as long-running (disabled by default)"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--enable-long"):
        return

    skip_long = pytest.mark.skip(reason="long test (use --enable-long to run)")
    for item in items:
        if "long" in item.keywords:
            item.add_marker(skip_long)
