from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog import StartMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select

from database.action_data_class import DataInteraction
from states.state_groups import startSG


async def sub_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    categories = await session.get_op()
    buttons = []
    count = 0
    for button in categories:
        buttons.append((button.name, button.link, count))
        count += 1
    return {
        'text': 'Чтобы дальше пользоваться ботом, пожалуйста подпишитесь на эти каналы',
        'items': buttons,
        'check_sub': 'Проверить подписку'
    }


async def check_sub(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    bot: Bot = dialog_manager.middleware_data.get('bot')
    channels = await session.get_op()
    for channel in channels:
        member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=clb.from_user.id)
        if member.status == 'left':
            await clb.answer('Вы не подписались на все каналы, пожалуйста попробуйте еще раз')
            return
    message = await clb.message.answer('Вы можете дальше пользоваться ботом')

    await dialog_manager.done()
    await clb.message.delete()
    await dialog_manager.start(startSG.start, mode=StartMode.RESET_STACK)