import asyncio
import logging
import os
import inspect
import pytz
import datetime

import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.router import router
from storage.nats_storage import NatsStorage
from utils.nats_connect import connect_to_nats
from services.start_consumer import start_transfer_consumer
from database.build import PostgresBuild
from database.model import Base
from database.action_data_class import setup_database, DataInteraction
from config_data.config import load_config, Config
from handlers.user_handlers import user_router
from dialogs import get_dialogs
from utils.schedulers import clean_applications
from middlewares import TransferObjectsMiddleware, RemindMiddleware


timezone = pytz.timezone('Europe/Moscow')
datetime.datetime.now(timezone)

module_path = inspect.getfile(inspect.currentframe())
module_dir = os.path.realpath(os.path.dirname(module_path))


format = '[{asctime}] #{levelname:8} {filename}:' \
         '{lineno} - {name} - {message}'

LOG_FILE = 'errors.log'

logging.basicConfig(
    level=logging.DEBUG,
    format=format,
    style='{'
)


logger = logging.getLogger(__name__)

config: Config = load_config()


async def main():
    database = PostgresBuild(config.db.dns)
    #await database.drop_tables(Base)
    #await database.create_tables(Base)
    session = database.session()
    await setup_database(session)

    scheduler: AsyncIOScheduler = AsyncIOScheduler()
    scheduler.start()
    db = DataInteraction(session)
    scheduler.add_job(
        clean_applications,
        'interval',
        args=[db],
        hours=4
    )


    #"""
    users = [await db.get_user(6225820635)]
    apps = [*await db.get_user_applications(6225820635)]
    applications = [f'{app.__dict__}\n' for app in apps]
    with open('user_apps.txt', 'a+', encoding='utf-8') as file:
        file.writelines([f'{user.__dict__}\n' for user in users])
        file.write('\n\n\n')
        file.writelines(applications)
    return
    #"""

    nc, js = await connect_to_nats(servers=config.nats.servers)
    #storage: NatsStorage = await NatsStorage(nc=nc, js=js).create_storage()

    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()#storage=storage)

    # подключаем роутеры
    dp.include_routers(user_router, *get_dialogs())

    # подключаем middleware
    dp.update.middleware(TransferObjectsMiddleware())
    dp.callback_query.middleware(RemindMiddleware())

    # запуск
    await bot.delete_webhook(drop_pending_updates=True)
    setup_dialogs(dp)

    logger.info('Bot start polling')

    app = FastAPI()
    app.include_router(router)
    app.state.nc = nc
    app.state.js = js
    app.state.scheduler = scheduler
    app.state.session = db

    uvicorn_config = uvicorn.Config(app, host='0.0.0.0', port=8000, log_level="info")  # ssl_keyfile='ssl/key.pem', ssl_certfile='ssl/cert.pem'
    server = uvicorn.Server(uvicorn_config)

    aiogram_task = asyncio.create_task(dp.start_polling(bot, _session=session, _scheduler=scheduler, js=js))
    uvicorn_task = asyncio.create_task(server.serve())
    consumer_task = asyncio.create_task(start_transfer_consumer(
        nc=nc,
        js=js,
        scheduler=scheduler,
        bot=bot,
        subject=config.consumer.subject,
        stream=config.consumer.stream,
        durable_name=config.consumer.durable_name
    ))

    try:
        await asyncio.gather(aiogram_task, uvicorn_task, consumer_task)
    except Exception as e:
        logger.exception(e)
    finally:
        await nc.close()
        logger.info('Connection closed')


if __name__ == "__main__":
    asyncio.run(main())