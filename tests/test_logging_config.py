import importlib
import logging
from types import ModuleType

import questions.logging_config as logging_config


def reset_root_logger():
    logger = logging.getLogger()
    for h in list(logger.handlers):
        logger.removeHandler(h)
    logger.setLevel(logging.NOTSET)


def reload_module(module: ModuleType) -> ModuleType:
    return importlib.reload(module)


def test_setup_logging_basic(monkeypatch):
    reload_module(logging_config)
    reset_root_logger()
    monkeypatch.setenv("COLOR_LOGS", "0")
    logging_config.setup_logging(level=logging.DEBUG)
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_setup_logging_level_env(monkeypatch):
    reload_module(logging_config)
    reset_root_logger()
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    logging_config.setup_logging()
    logger = logging.getLogger()
    assert logger.level == logging.ERROR


def test_get_logger_initializes(monkeypatch):
    reload_module(logging_config)
    reset_root_logger()
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    logger = logging_config.get_logger("test")
    assert isinstance(logger, logging.Logger)
