from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.style import Style

from dialogs.user_dialog import getters

from states.state_groups import startSG, adminSG, GiftsSG

user_dialog = Dialog(
    Window(
        DynamicMedia('media'),
        Const('🪐<b>Главное меню</b>\n\nC помощью <b>"Galaxy store"</b> вы можете приобрести '
              '<em>звезды ⭐️</em> и <em>Telegram premium 👑</em>'),
        Column(
            Button(Const('Купить звезды'), id='stars_pay_choose', on_click=getters.pay_choose, style=Style(emoji_id="5438496463044752972")),
            Button(Const('Купить премиум'), id='premium_pay_choose', on_click=getters.pay_choose, style=Style(emoji_id="5427168083074628963")),
            # Start(Const('Удаленные подарки'), id='gift_dialog', state=GiftsSG.choose_gift,
            #       style=Style(emoji_id="5203996991054432397")),
        ),
        Row(
            SwitchTo(Const('Реферальная программа'), id='ref_menu_switcher', state=startSG.ref_menu, style=Style(emoji_id="5388632425314140043")),
            SwitchTo(Const('Информация'), id='rules_menu_switcher', state=startSG.rules_menu, style=Style(emoji_id="5305265301917549162")),
        ),
        Column(
            SwitchTo(Const('Курс'), id='rate_menu_switcher', state=startSG.rate_menu, style=Style(emoji_id="5402186569006210455")),
            Url(Const('Тех. поддержка'), id='help_url', url=Const('https://t.me/GalaxyHelpers'), style=Style(emoji_id="5391032818111363540")),
        ),
        Start(Const('Админ панель'), id='admin', state=adminSG.start, when='admin'),
        getter=getters.start_getter,
        state=startSG.start
    ),
    Window(
        Format('{text}'),
        TextInput(
            id='get_currency_amount',
            on_success=getters.get_currency_amount
        ),
        Group(
            Select(
                Format('{item[0]}'),
                id='pay_menu_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.pay_menu_selector
            ),
            width=4
        ),
        Column(
            SwitchTo(Format('Получатель: {username}'), id='get_username_switcher', state=startSG.get_username, style=Style(emoji_id="5472239203590888751"))
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start, style=Style(emoji_id="5388584622328131561")),
        getter=getters.pay_menu_getter,
        state=startSG.pay_menu
    ),
    Window(
        Const('<tg-emoji emoji-id="5467730450002746997">🔍</tg-emoji><b>Укажите имя пользователя</b>\n<em>Н-р: @username</em>'),
        TextInput(
            id='get_username',
            on_success=getters.get_username
        ),
        SwitchTo(Const('Назад'), id='back_pay_menu', state=startSG.pay_menu, style=Style(emoji_id="5388584622328131561")),
        state=startSG.get_username
    ),
    Window(
        Const('Введите промокод или нажмите "➡️Пропустить", чтобы продолжить покупку звезд'),
        TextInput(
            id='get_promo',
            on_success=getters.get_promo
        ),
        Button(Const('➡️Пропустить'), id='skip_promo', on_click=getters.skip_promo),
        SwitchTo(Const('Назад'), id='back_pay_menu', state=startSG.pay_menu, style=Style(emoji_id="5388584622328131561")),
        state=startSG.get_promo
    ),
    Window(
        Format('{text}'),
        Column(
            Url(Const('Поделиться'), id='share_url', url=Format('{url}'), style=Style(emoji_id="5372849966689566579")),
            Button(Const('💰Вывести'), id='get_derive_amount_switcher', on_click=getters.get_derive_amount_switcher),
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start, style=Style(emoji_id="5388584622328131561")),
        getter=getters.ref_menu_getter,
        state=startSG.ref_menu
    ),
    Window(
        Const('ℹ️Пользовательское соглашение и политика конфиденциальности изложены ниже'),
        Column(
            Url(Const('🔗Политика конфиденциальности'), id='policy_url',
                url=Const('https://telegra.ph/Politika-konfidencialnosti-08-28-46')),
            Url(Const('🔗Пользовательское соглашение'), id='acceptable_url',
                url=Const('https://telegra.ph/Polzovatelskoe-soglashenie-08-28-18')),
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start, style=Style(emoji_id="5388584622328131561")),
        state=startSG.rules_menu
    ),
    Window(
        Format('{text}'),
        Column(
            Button(Const('Купить звезды'), id='stars_pay_choose', on_click=getters.pay_choose, style=Style(emoji_id="5438496463044752972")),
        ),
        SwitchTo(Const('Назад'), id='back', state=startSG.start, style=Style(emoji_id="5388584622328131561")),
        getter=getters.rate_menu_getter,
        state=startSG.rate_menu
    ),
    Window(
        Const('Введите сумму для вывода <em>(в Telegram stars⭐️)</em>'),
        TextInput(
            id='get_derive_amount',
            on_success=getters.get_derive_amount
        ),
        SwitchTo(Const('Назад'), id='back_ref_menu', state=startSG.ref_menu, style=Style(emoji_id="5388584622328131561")),
        state=startSG.get_derive_amount
    ),
)