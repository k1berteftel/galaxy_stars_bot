import asyncio
import random
from typing import Awaitable, Callable, Optional

from aiogram import Bot
from aiogram.types import Message


# ============================================================
#                      НАСТРОЙКИ МОДУЛЯ
# ============================================================

# Эмодзи, которые "мелькают" во время анимации
SPIN_EMOJIS = ["🧸", "⭐", "🎁", "💎", "🔥", "✨", "🎀", "🍀"]

# Длительность анимации (секунды)
SPIN_DURATION_MIN = 3.0
SPIN_DURATION_MAX = 6.0

# Частота обновления кадра анимации (секунды)
FRAME_INTERVAL = 0.18

# ID стикеров (замени на свои). Если None — стикер не отправляется.
STICKER_INTRO: Optional[str] = None      # стикер "открываем сундук"
STICKER_WIN: Optional[str] = None        # стикер "победа/салют"
STICKER_LOSE: Optional[str] = None       # стикер "не повезло"

# Текст подарка
GIFT_EMOJI = "🧸"
GIFT_NAME = "Плюшевый мишка"
GIFT_ID = '5170233102089322756'

# Тексты
TEXT_INTRO = "🎁 *Открываем подарок за покупку...*"
TEXT_SPINNING = "🎁 *Крутим барабаны...*"
TEXT_WIN = (
    "🎉 *ПОЗДРАВЛЯЕМ!* 🎉\n\n"
    "┌───┬───┬───┐\n"
    "│ ✨ │ " + GIFT_EMOJI + " │ ✨ │\n"
    "└───┴───┴───┘\n\n"
    f"Вы выиграли *{GIFT_NAME}* {GIFT_EMOJI}!\n"
    "Подарок придёт отдельным сообщением 📩"
)
TEXT_LOSE = (
    "😔 *В этот раз не повезло...*\n\n"
    "┌───┬───┬───┐\n"
    "│ ▫️ │ ▫️ │ ▫️ │\n"
    "└───┴───┴───┘\n\n"
    "Но удача улыбнётся в следующий раз! 🍀"
)


# ============================================================
#              ФУНКЦИЯ РАСЧЁТА ВЕРОЯТНОСТИ (ЗАГЛУШКА)
# ============================================================

async def calculate_chances(
    purchase_amount: int,
) -> bool:
    chance = 1 + ((purchase_amount - 50) * 0.1)
    return random.randint(1, 100) <= chance


# ============================================================
#                    ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

async def play_gift_roulette(
    bot: Bot,
    user_id: int,
    purchase_amount: int
) -> bool:
    """
    Запускает анимированный розыгрыш подарка.

    :param bot: объект aiogram.Bot
    :param user_id: ID пользователя (передаётся в probability_func)
    :param purchase_amount: сумма покупки в Stars
    """

    # 1. Определяем результат
    is_win: bool = await calculate_chances(purchase_amount)

    # 2. Вступительный стикер + текст
    if STICKER_INTRO:
        try:
            await bot.send_sticker(user_id, STICKER_INTRO)
        except Exception:
            pass  # стикер не критичен

    status_msg = await bot.send_message(
        chat_id=user_id,
        text=f"{TEXT_INTRO}\n\n┌───┬───┬───┐\n│ ❓ │ ❓ │ ❓ │\n└───┴───┴───┘",
        parse_mode="Markdown",
    )

    await asyncio.sleep(0.7)

    # 3. Анимация вращения
    await _run_spin_animation(bot, user_id, status_msg.message_id)

    # 4. Финальный кадр + стикер
    if is_win:
        await _finish_win(
            bot=bot,
            message_id=status_msg.message_id,
            user_id=user_id
        )
    else:
        await _finish_lose(bot, user_id, status_msg.message_id)

    return is_win


# ============================================================
#                    ВНУТРЕННИЕ ФУНКЦИИ
# ============================================================

async def _run_spin_animation(bot: Bot, chat_id: int, message_id: int) -> None:
    """Крутит барабаны: быстро в начале, медленно в конце."""
    duration = random.uniform(SPIN_DURATION_MIN, SPIN_DURATION_MAX)
    total_steps = max(int(duration / FRAME_INTERVAL), 10)

    for step in range(total_steps):
        # Рандомные символы для "шума"
        fake = [random.choice(SPIN_EMOJIS) for _ in range(3)]

        # Прогресс-бар
        filled = int((step + 1) / total_steps * 10)
        progress = "🟢" * filled + "⬜" * (10 - filled)

        # Эффект замедления: последние 30% шагов — медленнее
        if step > total_steps * 0.7:
            delay = FRAME_INTERVAL * 2.5
        else:
            delay = FRAME_INTERVAL

        text = (
            f"{TEXT_SPINNING}\n\n"
            f"┌───┬───┬───┐\n"
            f"│ {fake[0]} │ {fake[1]} │ {fake[2]} │\n"
            f"└───┴───┴───┘\n\n"
            f"{progress}"
        )

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="Markdown",
            )
        except Exception:
            # Игнорируем ошибки "message is not modified" и т.п.
            pass

        await asyncio.sleep(delay)


async def _finish_win(
    bot: Bot,
    message_id: int,
    user_id: int
) -> None:
    """Показывает победный результат и отправляет мишку."""
    # Победный стикер
    win_sticker = STICKER_WIN
    if win_sticker:
        try:
            await bot.send_sticker(user_id, win_sticker)
        except Exception:
            pass

    try:
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=TEXT_WIN,
            parse_mode="Markdown"
        )
    except Exception:
        pass

    await bot.send_gift(
        gift_id=GIFT_ID,
        user_id=user_id
    )


async def _finish_lose(bot: Bot, chat_id: int, message_id: int) -> None:
    """Показывает проигрышный результат."""
    if STICKER_LOSE:
        try:
            await bot.send_sticker(chat_id, STICKER_LOSE)
        except Exception:
            pass

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=TEXT_LOSE,
            parse_mode="Markdown",
        )
    except Exception:
        pass