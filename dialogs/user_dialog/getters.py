import os
from aiogram.types import CallbackQuery, User, Message, ContentType, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput

from utils.tables import get_table
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
        if not (50 <= currency < 100000):
            await msg.delete()
            await msg.answer('❗️Кол-во звезд должно быть быть не меньше 50 и не больше 100000')
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


async def get_derive_amount_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(clb.from_user.id)
    if user.earn < 100:
        await clb.answer('❗️Сумма для вывода 100 звезд или более .')
        return
    await dialog_manager.switch_to(startSG.get_derive_amount)


async def get_derive_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        amount = int(text)
    except Exception:
        await msg.delete()
        await msg.answer('❗️Сумма для вывода должна быть числом, пожалуйста попробуйте снова')
        return
    if amount < 50:
        await msg.answer('❗️Сумма для вывода не может быть меньше 50')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    msg_user = await session.get_user(msg.from_user.id)
    if amount > msg_user.earn:
        await msg.answer('❗️Сумма для вывода должна быть не больше той что сейчас у вас')
        return
    username = msg.from_user.username
    if not username:
        await msg.answer(text='❗️Чтобы получить звезды, пожалуйста поставьте на свой аккаунт юзернейм')
        return
    ref_users = await session.get_ref_users(msg.from_user.id)
    users = []
    for user in ref_users:
        users.append(
            [
                user.user_id,
                user.name,
                '@' + user.username if user.username else '-',
                user.refs,
                user.entry.strftime('%d-%m-%Y %H:%M')
            ]
        )
    users.insert(0, ['User Id', 'Никнейм', 'Юзернейм', 'Рефералы', 'Первый запуск'])
    table_1 = get_table(users, 'Рефералы')
    sub_users = []
    sub_ref_users = await session.get_sub_ref_users(msg.from_user.id)
    for user in sub_ref_users:
        sub_users.append(
            [
                user.user_id,
                user.name,
                '@' + user.username if user.username else '-',
                user.refs,
                user.entry.strftime('%d-%m-%Y %H:%M')
            ]
        )
    sub_users.insert(0, ['User Id', 'Никнейм', 'Юзернейм', 'Рефералы', 'Первый запуск'])
    table_2 = get_table(sub_users, 'Рефералы 2')
    text = (f'<b>Заявка на вывод средств</b>\n\nДанные о пользователе:\n'
            f'- Никнейм: {msg_user.name}\n - Username: @{msg_user.username}'
            f'\n - Telegram Id: {msg.from_user.id}\n - Рефералы: {msg_user.refs}\n - Рефералы 2: {msg_user.sub_refs}'
            f'\n - Общий баланс: {msg_user.earn}⭐️\n - <b>Сумма для вывода</b>: {amount}⭐️')
    builder = MediaGroupBuilder(caption=text)
    builder.add_document(FSInputFile(path=table_1))
    builder.add_document(FSInputFile(path=table_2))
    await msg.bot.send_media_group(
        media=builder.build(),
        chat_id=config.bot.admin_ids[0],
    )
    try:
        os.remove(table_1)
        os.remove(table_2)
    except Exception:
        ...
    await session.update_earn(msg.from_user.id, -amount)
    await msg.answer('✅Заявка на вывод средств была успешно отправлена')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.ref_menu)


async def rate_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    prices = await session.get_prices()
    usdt_rub = await _get_usdt_rub()
    usdt_ton = await _get_ton_usdt()
    ton_rub = round(usdt_ton * usdt_rub, 4)
    usdt = (await get_stars_price(50)) / 50
    print(usdt)
    amount = round((usdt * usdt_rub) / (1 - prices.stars_charge / 100), 2)
    usdt = round(amount / usdt_rub, 3)
    ton = round(usdt / usdt_ton, 6)
    text = (f'<b>🪙 Актуальные курсы:</b><em>\n\t 1⭐️- {amount}₽\n\t1⭐️- {usdt}$\n\t1⭐️- {ton} TON</em>'
            f'\n<b> - 1 USDT = {usdt_rub}₽\n - 1 TON = {ton_rub}₽</b>')
    return {'text': text}

