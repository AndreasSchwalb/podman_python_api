import logging

from extended_config_parser import ExtendedConfigParser


class Logger:
    @staticmethod
    def setup(logger_name: str) -> logging.Logger:
        config = ExtendedConfigParser()
        logger = logging.getLogger(logger_name)
        log_level = Logger.get_log_level_by_str(config['logging']['log_level'])
        logger.setLevel(log_level)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s--%(levelname)s--%(message)s')
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)
        return logger

    @staticmethod
    def get_log_level_by_str(log_level: str) -> int:

        if log_level == 'debug':
            return logging.DEBUG
        elif log_level == 'info':
            return logging.INFO
        elif log_level == 'warn':
            return logging.WARNING
        elif log_level == 'error':
            return logging.ERROR
        elif log_level == 'critical':
            return logging.CRITICAL
        else:
            return logging.INFO
