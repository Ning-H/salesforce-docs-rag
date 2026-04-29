import logging
import os
import sys


def configure_logging(level: str = "INFO") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    if os.getenv("AIRFLOW_CTX_DAG_ID"):
        logging.getLogger("salesforce_docs_rag").setLevel(log_level)
        return

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
