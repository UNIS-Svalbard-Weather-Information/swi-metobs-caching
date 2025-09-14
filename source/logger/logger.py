# SPDX-FileCopyrightText: 2025 Louis Pauchet <louis.pauchet@insa-rouen.fr>
# SPDX-License-Identifier:  EUPL-1.2

from loguru import logger

class Logger:
    @staticmethod
    def setup_logger(name):
        """
        Set up and configure a logger with a specified name.

        This static method creates and configures a logger instance identified by the given name. It ensures that the logger
        outputs log messages to the console using a StreamHandler with a standardized message format that includes the timestamp,
        logger name, log level, and the log message itself. If a logger with the same name has already been configured with handlers,
        this method avoids adding duplicate handlers. The logger's level is explicitly set to INFO by default.

        Args:
            name (str): The identifier for the logger. This is typically set to the module or class name to help distinguish log
                        messages coming from different parts of the application.

        Returns:
            logging.Logger: A logger instance configured with:
                - A StreamHandler for outputting logs to the console.
                - A formatter that produces log messages in the format:
                  '%(asctime)s - %(name)s - %(levelname)s - %(message)s'.
                - A logging level set to INFO.
        """
        # logger = logging.getLogger(name)

        # # Avoid adding multiple handlers if the logger is already configured
        # if not logger.hasHandlers():
        #     handler = logging.StreamHandler()
        #     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #     handler.setFormatter(formatter)
        #     logger.addHandler(handler)

        # # Explicitly set the logger's level
        # logger.setLevel(logging.INFO)

        return logger
