from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def make_row_keyboard(items: list[tuple[str, str] | str], inline: bool | None) -> ReplyKeyboardMarkup | InlineKeyboardMarkup:
    if inline:
        row = [[InlineKeyboardButton(text=item[0], callback_data=item[1]) for item in items]]
        return InlineKeyboardMarkup(inline_keyboard=row)
    else:
        row = [KeyboardButton(text=item) for item in items]
        return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)
