import logging


def setup_logging(app_name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logging.getLogger(app_name)
