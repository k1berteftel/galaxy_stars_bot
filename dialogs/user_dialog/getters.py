from aiogram.types import CallbackQuery, User, Message, ContentType
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput

from utils.transactions import get_stars_price
from utils.payments.create_payment import _get_usdt_rub, _get_ton_usdt
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG, PaymentSG


config: Config = load_config()


async def start_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admin = False
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    if event_from_user.id in admins:
        admin = True
    media = MediaAttachment(type=ContentType.PHOTO, path='photos/galaxy_menu.png')
    return {
        'media': media,
        'admin': admin
    }


async def pay_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data.clear()
    rate = clb.data.split('_')[0]
    dialog_manager.dialog_data['rate'] = rate
    await dialog_manager.switch_to(state=startSG.pay_menu)


async def pay_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    rate = dialog_manager.dialog_data.get('rate')
    username = dialog_manager.dialog_data.get('username')
    if not username:
        username = '@' + event_from_user.username
        dialog_manager.dialog_data['username'] = username
    if rate == 'stars':
        text = (f'<b>⭐️Покупка Telegram Stars</b>\n - Получатель: {username}\n\n'
                f'<em>Чтобы поменять кол-во звезд для покупки <b>введите кол-во звезд текстом👇 '
                f'(от 50 до 1000000)</b></em>')
        buttons = [
            ('50', '50'),
            ('100', '100'),
            ('500', '500'),
            ('1000', '1000')
        ]
    else:
        text = (f'<b>Покупка Telegram Premium</b>\n - Получатель: {username}\n\n'
                f'<em>Чтобы продолжить выберите внизу тариф подписки👇 </em>')
        buttons = [
            ('3 месяца', '3'),
            ('6 месяцев', '6'),
            ('12 месяцев', '12')
        ]
    return {
        'text': text,
        'items': buttons,
        'username': username
    }


async def get_currency_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    rate = dialog_manager.dialog_data.get('rate')
    if rate == 'stars':
        try:
            currency = int(text)
        except Exception:
            await msg.delete()
            await msg.answer('❗️Кол-во звезд должно быть числом, пожалуйста попробуйте снова')
            return
        if not (50 <= currency < 1000000):
            await msg.delete()
            await msg.answer('❗️Кол-во звезд должно быть быть не меньше 50 и не больше 1000000')
            return
        dialog_manager.dialog_data['currency'] = currency
        await dialog_manager.switch_to(startSG.get_promo)
        return
    await msg.delete()
    await dialog_manager.switch_to(startSG.pay_menu)


async def pay_menu_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['currency'] = int(item_id)
    rate = dialog_manager.dialog_data.get('rate')
    if rate == 'stars':
        await dialog_manager.switch_to(startSG.get_promo)
        return
    rate = dialog_manager.dialog_data.get('rate')
    username = dialog_manager.dialog_data.get('username')
    currency = dialog_manager.dialog_data.get('currency')
    start_data = {'rate': rate, 'username': username, 'currency': currency}
    await dialog_manager.start(PaymentSG.menu, data=start_data)


async def get_username(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    text = text.strip()
    if not text.startswith('@'):
        await msg.delete()
        await msg.answer('❗️Юзернейм должен начинать со знака "@", пожалуйста попробуйте снова')
        return
    if ' ' in text:
        await msg.delete()
        await msg.answer('❗Юзернейм должен быть в формате "@username", пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['username'] = text
    await dialog_manager.switch_to(startSG.pay_menu)


async def get_promo(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    promo = await session.check_promo(msg.from_user.id, text)
    if not promo:
        await msg.answer('😔К сожалению такого промокода не было найдено или же вы уже вводили его')
        return
    await msg.answer('✅Промокод был успешно активирован')
    dialog_manager.dialog_data['promo'] = promo.percent
    rate = dialog_manager.dialog_data.get('rate')
    username = dialog_manager.dialog_data.get('username')
    currency = dialog_manager.dialog_data.get('currency')
    start_data = {'rate': rate, 'username': username, 'currency': currency, 'promo': promo.percent}
    await dialog_manager.start(PaymentSG.menu, data=start_data)


async def skip_promo(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    rate = dialog_manager.dialog_data.get('rate')
    username = dialog_manager.dialog_data.get('username')
    currency = dialog_manager.dialog_data.get('currency')
    start_data = {'rate': rate, 'username': username, 'currency': currency}
    await dialog_manager.start(PaymentSG.menu, data=start_data)


async def ref_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    text = (f'🎁<b>Реферальная программа</b>\n🔗Ваша ссылка:\n\t'
            f'<code>t.me/GalaxyStoreStarBot?start={event_from_user.id}</code>\n\n'
            f'<blockquote>Вы получаете по 2% от каждой покупки вашего реферала</blockquote>'
            f'\n - 👤Рефералы (lvl-1): {user.refs}\n - '
            f'💰Всего заработано: {user.earn}⭐️')  # 👥Рефералы (lvl-2): {user.sub_refs}\n -
    return {
        'text': text,
        'url': f'http://t.me/share/url?url=https://t.me/GalaxyStoreStarBot?start={event_from_user.id}'
    }


async def rate_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    prices = await session.get_prices()
    usdt_rub = await _get_usdt_rub()
    usdt_ton = await _get_ton_usdt()
    ton_rub = round(usdt_ton * usdt_rub, 4)
    usdt = await get_stars_price(1)
    print(usdt)
    amount = round((usdt * usdt_rub) / (1 - prices.stars_charge / 100), 2)
    usdt = round(amount / usdt_rub, 3)
    ton = round(usdt / usdt_ton, 6)
    text = (f'<b>🪙 Актуальные курсы:</b><em>\n\t 1⭐️- {amount}₽\n\t1⭐️- {usdt}$\n\t1⭐️- {ton} TON</em>'
            f'\n<b> - 1 USDT = {usdt_rub}₽\n - 1 TON = {ton_rub}₽</b>')
    return {'text': text}

