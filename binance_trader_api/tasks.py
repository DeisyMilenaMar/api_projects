import logging

from api.config.celery_setup import app
from binance_trader_api.services import PriceMonitoringService

logger = logging.getLogger(__name__)

TASK_NAME = "binance_trader.tasks.check_price_task"


@app.task
def check_price_task():
    """
    Celery task that periodically checks prices for pending transactions and
    sends notifications when target prices are reached.
    """
    try:
        service = PriceMonitoringService()
        result = service.monitor_and_notify_price()

        return f"Task {TASK_NAME} completed successfully. Result: {result}"

    except Exception as exc:
        logger.error(f"Task {TASK_NAME} failed: {str(exc)}", exc_info=True)

        return f"Task {TASK_NAME} failed: {str(exc)}"
