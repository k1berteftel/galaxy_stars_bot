import asyncio
import aiohttp
import json
import logging
from functools import wraps

from pyrogram import Client
from config_data.config import load_config, Config

from utils.payments.create_payment import _get_ton_usdt


logger = logging.getLogger(__name__)
config: Config = load_config()


app = Client(config.user_bot.session, api_id=config.user_bot.api_id, api_hash=config.user_bot.api_hash)
BASE_URL = 'https://fragbridge.ru'


headers = {
    'Api-Key': config.fragment.api_key
}


def retry_request_decorator(max_retries=2, delay=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            counter = 0
            while True:
                if counter >= max_retries:
                    return None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    counter += 1
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


async def get_stars_price(amount: int) -> float:
    url = BASE_URL + '/rate/stars'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as resp:
            data = await resp.json()
            print(data)
            usdt_per_star = data.get('usdt_per_star')
    return round(usdt_per_star * amount, 5)


#print(asyncio.run(get_stars_price(50)))


async def transfer_stars(username: str, stars: int) -> bool:
    url = BASE_URL + 'purchase/stars'
    data = {
        "currency":  int(stars),
        "receiver": username,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status not in [200, 201]:
                return False
            if not data['ok']:
                logger.error(f'Transfer stars error - {data.get("code")}: {data.get("message")}')
                return False
    return True


async def transfer_premium(username: str, months: int):
    url = BASE_URL + 'purchase/premium'
    data = {
        "currency":  months,
        "receiver": username,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status not in [200, 201]:
                return False
            data = await response.json()
            if not data['ok']:
                logger.error(f'Transfer premium error - {data.get("code")}: {data.get("message")}')
                return False
    return True


async def transfer_ton(username: str, amount: int):
    url = 'https://tg.parssms.info/v1/ads/topup'
    data = {
        "query": username,
        "amount": str(amount)
    }
    headers = {
        'Content-Type': 'application/json',
        'api-key': config.fragment.api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers, ssl=False) as resp:
            print(resp.status)
            if resp.status not in [200, 201]:
                print(await resp.content.read())
                logging.error(await resp.content.read())
                try:
                    logging.error(await resp.json())
                except Exception:
                    ...
                return False
            data = await resp.json()
            if data['ok'] != True:
                logging.error(data)
                return False
            print(data)
    return True


async def check_user_premium(username: str):
    url = BASE_URL + 'check/premium'
    data = {
        "username": username
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status not in [200, 201]:
                logger.error(f'Error while check user premium request: {await response.text()}')
                return False
            data = await response.json()
    return data.get('is_premium')


@retry_request_decorator()
async def transfer_gift(username: str, currency: int):
    async with app:
        try:
            msg = await app.send_gift(
                chat_id=username,
                gift_id=currency,
                is_private=True
            )
            return True
        except Exception as err:
            raise err
    return False


# BASE_URL = 'https://robynhood.parssms.info/'
#
#
# headers = {
#     'X-API-Key': config.fragment.api_key
# }
#
# app = Client(config.user_bot.session, api_id=config.user_bot.api_id, api_hash=config.user_bot.api_hash)
#
#
# def subgram_api_decorator(max_retries=2, delay=5):
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             counter = 0
#             while True:
#                 if counter >= max_retries:
#                     return None
#                 try:
#                     result = await func(*args, **kwargs)
#                     return result
#                 except Exception:
#                     counter += 1
#                     await asyncio.sleep(delay)
#         return wrapper
#     return decorator
#
#
# @subgram_api_decorator()
# async def get_stars_price(amount: int) -> float:
#     url = BASE_URL + 'api/prices'
#     data = {
#         'product_type': 'stars',
#         'quantity': str(amount)
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, params=data, headers=headers, ssl=False) as resp:
#             if resp.status not in [200, 201]:
#                 try:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'JSON получения цены: {await resp.json()}\n\n')
#                 except Exception:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'Content получения цены: {await resp.text()}\n\n')
#                 raise Exception
#             data = await resp.json()
#             ton = await _get_ton_usdt()
#     return round(float(data['price']) * ton, 5)
#
#
# @subgram_api_decorator()
# async def transfer_stars(username: str, stars: int) -> bool:
#     url = BASE_URL + 'api/purchase'
#     data = {
#         "product_type": "stars",
#         "recipient": username,
#         "quantity":  str(stars),
#         #"idempotency_key": config.fragment.api_key
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=data, headers=headers) as response:
#             if response.status not in [200, 201]:
#                 try:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'JSON транзакции:{await response.json()}\n\n')
#                 except Exception:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'Content транзакции:{await response.text()}\n\n')
#                 return False
#             data = await response.json()
#             print(data)
#     return True
#
#
# @subgram_api_decorator()
# async def transfer_premium(username: str, months: int):
#     url = BASE_URL + 'api/purchase'
#     data = {
#         "product_type": "premium",
#         "recipient": username,
#         "months": str(months),
#         #"idempotency_key": config.fragment.api_key
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=data, headers=headers) as response:
#             if response.status not in [200, 201]:
#                 try:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'JSON Premium:{await response.json()}\n\n')
#                 except Exception:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'Content Premium:{await response.text()}\n\n')
#                 return False
#             data = await response.json()
#             print(data)
#     return True
#
#
# @subgram_api_decorator()
# async def transfer_ton(username: str, amount: int):
#     url = 'https://tg.parssms.info/v1/ads/topup'
#     data = {
#         "query": username,
#         "amount": str(amount)
#     }
#     headers = {
#         'Content-Type': 'application/json',
#         'api-key': config.fragment.api_key
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=data, headers=headers, ssl=False) as resp:
#             print(resp.status)
#             if resp.status not in [200, 201]:
#                 print(await resp.content.read())
#                 logging.error(await resp.content.read())
#                 try:
#                     logging.error(await resp.json())
#                 except Exception:
#                     ...
#                 return False
#             data = await resp.json()
#             if data['ok'] != True:
#                 logging.error(data)
#                 return False
#             print(data)
#     return True
#
#
# @subgram_api_decorator()
# async def check_user_premium(username: str, months: int):
#     url = BASE_URL + 'api/test/purchase'
#     data = {
#         "product_type": "premium",
#         "recipient": username,
#         "months": str(months),
#         #"idempotency_key": config.fragment.api_key
#     }
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=data, headers=headers) as response:
#             if response.status not in [200, 201]:
#                 try:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'JSON Premium:{await response.json()}\n\n')
#                 except Exception:
#                     with open('err_trans.txt', 'a', encoding='utf-8') as f:
#                         f.write(f'Content Premium:{await response.text()}\n\n')
#                 return False
#             data = await response.json()
#             print(data)
#     return True
#
#
# async def transfer_gift(username: str, currency: int):
#     async with app:
#         try:
#             msg = await app.send_gift(
#                 chat_id=username,
#                 gift_id=currency,
#                 is_private=True
#             )
#             return True
#         except Exception as err:
#             raise err
#     return False
#
#
#
# #print(asyncio.run(get_stars_price(50)))