import datetime
import json
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import APIRouter, Request, Form, HTTPException, status
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from nats.js import JetStreamContext

from services.publisher import send_publisher_data
from database.action_data_class import DataInteraction
from utils.transactions import transfer_stars, transfer_ton, transfer_premium
from config_data.config import load_config, Config


config: Config = load_config()

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/payment")
async def ping(response: Request, us_userId: str | int = Form(...), CUR_ID: str | int = Form(...), us_appId: str | int = Form(...)):
    print(response.__dict__)
    user_id = int(us_userId)
    session: DataInteraction = response.app.state.session
    scheduler: AsyncIOScheduler = response.app.state.scheduler
    js: JetStreamContext = response.app.state.js
    application = await session.get_application(int(us_appId))
    if application.status in [0, 2, 3]:
        return "OK"
    trans_type = int(CUR_ID)
    payment = ''
    if trans_type == 36:
        payment = 'card'
    if trans_type == 44:
        payment = 'sbp'
    data = {
        'transfer_type': application.type,
        'username': application.receiver,
        'currency': application.amount,
        'payment': payment,
        'app_id': application.uid_key
    }
    await send_publisher_data(
        js=js,
        subject=config.consumer.subject,
        data=data
    )
    job = scheduler.get_job(f'payment_{user_id}')
    if job:
        job.remove()
    stop_job = scheduler.get_job(f'stop_payment_{user_id}')
    if stop_job:
        stop_job.remove()
    return "OK"


@router.post('/paycore')
async def handle_paycore(response: Request):
    logger.info('Catch paycore-post request')
    session: DataInteraction = response.app.state.session
    scheduler: AsyncIOScheduler = response.app.state.scheduler
    js: JetStreamContext = response.app.state.js
    logger.info('Trying to get json of request')
    try:
        data = await response.json()
        logger.info(f'Parse json: {data}')
    except Exception as err:
        logger.error(f'Error while parse json: {err}')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Payload is not allowed"
        )

    logger.info('Get paycore order_id data')
    order_id = data.get('order_id')
    paycore_app = await session.get_paycore_app_by_order_id(order_id)
    application = await session.get_application(paycore_app.app_id)
    user_id = application.user_id

    logger.info(f'Application ID: {application.uid_key}, status: {application.status}')
    if application.status in [0, 2, 3]:
        return "OK"

    payment = data.get('method')
    data = {
        'transfer_type': application.type,
        'username': application.receiver,
        'currency': application.amount,
        'payment': payment,
        'app_id': application.uid_key
    }
    logger.info(f'Sending "{data}" to consumer')
    await send_publisher_data(
        js=js,
        subject=config.consumer.subject,
        data=data
    )
    job = scheduler.get_job(f'payment_{user_id}')
    if job:
        job.remove()
    stop_job = scheduler.get_job(f'stop_payment_{user_id}')
    if stop_job:
        stop_job.remove()
    return "OK"
