import logging

class Logger:
    @staticmethod
    def setup_logger(name):
        """
        Set up a logger for the given name.

        Args:
            name (str): The name for the logger.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)

        # Avoid adding multiple handlers if the logger is already configured
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Explicitly set the logger's level
        logger.setLevel(logging.INFO)

        return logger
