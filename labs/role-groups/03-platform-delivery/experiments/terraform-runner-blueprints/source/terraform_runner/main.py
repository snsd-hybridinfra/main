from __future__ import annotations

import logging
import time

import httpx

from .client import ApprovalClient
from .config import Settings
from .executor import Executor


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("terraform-runner")


def run_forever(settings: Settings | None = None) -> None:
    runner_settings = settings or Settings.from_env()
    client = ApprovalClient(runner_settings)
    executor = Executor(runner_settings)
    logger.info("runner started id=%s mode=%s", runner_settings.runner_id, runner_settings.runner_mode)
    while True:
        try:
            job = client.claim()
            if job is None:
                time.sleep(max(0.2, runner_settings.poll_interval_seconds))
                continue
            logger.info(
                "claimed job=%s operation=%s module=%s",
                job["job_id"],
                job["operation"],
                job["module_name"],
            )
            executor.run(job, lambda payload: client.report(str(job["job_id"]), payload))
        except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
            logger.error("runner loop failed: %s", exc)
            time.sleep(max(0.5, runner_settings.poll_interval_seconds))


if __name__ == "__main__":
    run_forever()
