from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.style import Style

from dialogs.payment_dialog import getters

from states.state_groups import startSG, PaymentSG


payment_dialog = Dialog(
    Window(
        Const('🏦<b>Выберите способ оплаты</b>\n'),
        Format('{text}'),
        Column(
            Button(Const('CryptoBot'), id='cb_payment_choose', on_click=getters.payment_choose, style=Style(emoji_id="5361836987642815474")),
            Button(Const('Крипта'), id='crypto_payment_choose', on_click=getters.payment_choose, style=Style(emoji_id="6213220344614882714")),
            Button(Const('Карта'), id='card_payment_choose', on_click=getters.payment_choose, style=Style(emoji_id="5801180866071760635")),
            Button(Const('СБП'), id='sbp_payment_choose', on_click=getters.payment_choose, style=Style(emoji_id="5265074015868822600")),
        ),
        Cancel(Const('Назад'), id='close_dialog', style=Style(emoji_id="5388584622328131561")),
        getter=getters.menu_getter,
        state=PaymentSG.menu
    ),
    Window(
        Const('<b>⌛️Ожидание оплаты</b>'),
        Format('{text}'),
        Column(
            Url(Const('🔗Оплатить'), id='url', url=Format('{url}')),
        ),
        Button(Const('Назад'), id='back', on_click=getters.close_payment, style=Style(emoji_id="5388584622328131561")),
        getter=getters.process_payment_getter,
        state=PaymentSG.process_payment
    ),
)