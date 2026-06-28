import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def start_scheduler():
    from app.services.caixa_ingestion import sync_all_ufs
    from app.services.santander_ingestion import sync_santander
    from app.services.biasi_ingestion import sync_biasi

    scheduler.add_job(
        lambda: asyncio.create_task(sync_all_ufs()),
        CronTrigger(hour=3, minute=0),  # 3h da manhã horário de Brasília
        id="sync_caixa",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        lambda: asyncio.create_task(sync_santander()),
        CronTrigger(hour=4, minute=0),  # 4h da manhã
        id="sync_santander",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        lambda: asyncio.create_task(sync_biasi()),
        CronTrigger(hour=5, minute=0),  # 5h da manhã
        id="sync_biasi",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("Scheduler iniciado — syncs agendados: Caixa 3h, Santander 4h, Biasi 5h BRT")


def stop_scheduler():
    scheduler.shutdown(wait=False)
