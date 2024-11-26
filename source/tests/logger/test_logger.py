import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import logging
from io import StringIO
import pytest
from source.logger.logger import Logger


@pytest.fixture
def log_stream():
    """
    Pytest fixture to create a log stream for capturing log outputs.
    """
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    return stream, handler


def test_logger_initialization(log_stream):
    """
    Test that the logger is properly initialized with the correct name and level.
    """
    logger_name = "TestLogger"
    logger = Logger.setup_logger(logger_name)

    stream, handler = log_stream
    logger.addHandler(handler)

    # Check logger name and level
    assert logger.name == logger_name
    assert logger.level == logging.INFO


def test_logger_single_handler():
    """
    Test that the logger avoids adding duplicate handlers.
    """
    logger_name = "TestLoggerSingleHandler"
    logger = Logger.setup_logger(logger_name)

    # Capture the initial number of handlers
    initial_handler_count = len(logger.handlers)
    logger = Logger.setup_logger(logger_name)
    # Ensure no new handlers are added
    assert len(logger.handlers) == initial_handler_count


def test_logger_output(log_stream):
    """
    Test that the logger outputs messages in the correct format.
    """
    logger_name = "TestLoggerOutput"
    logger = Logger.setup_logger(logger_name)

    stream, handler = log_stream
    logger.addHandler(handler)

    # Generate a log message
    test_message = "This is a test message."
    logger.info(test_message)
    handler.flush()

    # Check the captured log message format
    log_output = stream.getvalue()
    assert test_message in log_output
    assert logger_name in log_output
    assert "INFO" in log_output


@pytest.fixture(autouse=True)
def clean_loggers():
    """
    Fixture to clean up loggers after each test to avoid side effects.
    """
    yield
    logging.shutdown()
