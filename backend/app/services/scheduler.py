import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def start_scheduler():
    from app.services.caixa_ingestion import sync_all_ufs

    scheduler.add_job(
        lambda: asyncio.create_task(sync_all_ufs()),
        CronTrigger(hour=3, minute=0),  # 3h da manhã horário de Brasília
        id="sync_caixa",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("Scheduler iniciado — sync Caixa agendado para 3h BRT")


def stop_scheduler():
    scheduler.shutdown(wait=False)
