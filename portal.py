import asyncio
import logging
import json
import os
import random
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9264454314:AAGu6P1Xp0_zJvWLh_NhpKM0mrGr6x93uRE"
MAIN_ADMIN_ID = 8941873700
SETTINGS_FILE = "settings.json"
DEALS_FILE = "deals.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ССЫЛКИ ---
LINK_PORTALS = "https://t.me/portals?startapp="
LINK_SUPPORT = "https://t.me/Portalldeal"

# --- ДЕФОЛТНЫЕ ТЕКСТЫ (если вы их не меняли через /ruvire) ---
DEFAULT_TEXTS = {
    "welcome": "<b>Portals Guarant - #1 По трейдингу NFT подарков.</b>\n\nПокупайте и продавайте всё, что угодно — безопасно, ведь нас выбирают более 500k пользователей!\n\n• Удобное управление кошельками\n• Безопасные сделки с гарантией\n• 0% Комиссия\n\nВыберите нужный раздел ниже:\n\nПоддержка 24/7: Менеджер",
    "choose_method": "<b>Выберите метод оплаты:</b>",
    "choose_amount": "<b>Введите сумму сделки.</b>\n\nПример: 100.25",
    "choose_currency": "<b>Выберите валюту:</b>",
    "enter_nft": "<b>Ссылка на NFT</b>\n\nОтправьте ссылку (t.me/nft/...):"
}

# --- СОСТОЯНИЯ (FSM) ---
class DealStates(StatesGroup):
    entering_amount = State()
    choosing_currency = State()
    entering_nft_link = State()

class AdminStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_new_value = State()

# --- ФУНКЦИИ РАБОТЫ С НАСТРОЙКАМИ ---
def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"texts": {}, "images": {}, "admins": []}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_text(key):
    settings = get_settings()
    return settings.get("texts", {}).get(key, DEFAULT_TEXTS.get(key, "Текст не задан"))

def get_image(key):
    settings = get_settings()
    return settings.get("images", {}).get(key)

def is_admin(user_id):
    if user_id == MAIN_ADMIN_ID: return True
    return user_id in get_settings().get("admins", [])

# --- ФУНКЦИИ ДЛЯ СДЕЛОК ---
def get_deals():
    if os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_deals(deals):
    with open(DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=4)

def generate_deal_id():
    chars = string.ascii_uppercase + string.digits
    return f"#{''.join(random.choice(chars) for _ in range(7))}"

def find_deal(deal_id):
    for deal in get_deals():
        if deal["deal_id"] == deal_id:
            return deal
    return None

def update_deal_status(deal_id, new_status):
    deals = get_deals()
    for deal in deals:
        if deal["deal_id"] == deal_id:
            deal["status"] = new_status
            break
    save_deals(deals)

# --- ОТПРАВКА ЭКРАНА (с проверкой картинки) ---
async def send_screen(chat_id, text_key, reply_markup, edit_message: types.Message = None, parse_mode="HTML"):
    text = get_text(text_key)
    photo = get_image(text_key)

    if edit_message:
        try:
            await edit_message.delete()
        except:
            pass

    if photo:
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)

# --- КЛАВИАТУРЫ ---
def get_main_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Создать сделку", callback_data="create_deal"))
    builder.row(
        InlineKeyboardButton(text="Кошелек", callback_data="wallet"),
        InlineKeyboardButton(text="Мои сделки", callback_data="my_deals")
    )
    builder.row(InlineKeyboardButton(text="Portals Market", url=LINK_PORTALS))
    builder.row(InlineKeyboardButton(text="Язык", callback_data="language_menu"))
    builder.row(InlineKeyboardButton(text="Поддержка", url=LINK_SUPPORT))
    
    if is_admin(user_id):
        builder.row(InlineKeyboardButton(text="Админ-панель", callback_data="admin_panel"))
    return builder.as_markup()

def get_payment_method_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Кошелек", callback_data="pay_wallet"),
        InlineKeyboardButton(text="Карта", callback_data="pay_card"),
        InlineKeyboardButton(text="Звезды", callback_data="pay_stars")
    )
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_currency_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="RUB", callback_data="cur_RUB"),
        InlineKeyboardButton(text="UAH", callback_data="cur_UAH"),
        InlineKeyboardButton(text="USDT", callback_data="cur_USDT")
    )
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back_to_amount"))
    return builder.as_markup()

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await send_screen(message.chat.id, "welcome", get_main_keyboard(message.from_user.id))

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_screen(callback.message.chat.id, "welcome", get_main_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

# --- КОШЕЛЕК ---
@dp.callback_query(F.data == "wallet")
async def wallet_menu(callback: types.CallbackQuery):
    text = "<b>Ваш кошелек</b>\n\nБаланс: 0.00 TON\nВ сделках: 0.00 TON"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить", callback_data="stub")],
        [InlineKeyboardButton(text="В главное меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- СОЗДАНИЕ СДЕЛКИ ---
@dp.callback_query(F.data == "create_deal")
async def start_deal(callback: types.CallbackQuery, state: FSMContext):
    await send_screen(callback.message.chat.id, "choose_method", get_payment_method_keyboard(), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(payment_method=method)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Валюта", callback_data="choose_currency")],
        [InlineKeyboardButton(text="Назад", callback_data="create_deal")]
    ])
    await send_screen(callback.message.chat.id, "choose_amount", kb, edit_message=callback.message)
    await state.set_state(DealStates.entering_amount)
    await callback.answer()

@dp.message(DealStates.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    amount = message.text.replace(",", ".")
    try:
        float(amount)
    except ValueError:
        await message.answer("Введите корректное число (например, 100 или 50.5).")
        return
        
    data = await state.get_data()
    if "currency" not in data:
        await state.update_data(currency="RUB")
        
    await state.update_data(amount=amount)
    
    await send_screen(message.chat.id, "choose_currency", get_currency_keyboard())
    await state.set_state(DealStates.choosing_currency)

@dp.callback_query(DealStates.choosing_currency, F.data.startswith("cur_"))
async def choose_currency(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_amount")]
    ])
    await send_screen(callback.message.chat.id, "enter_nft", kb, edit_message=callback.message)
    await state.set_state(DealStates.entering_nft_link)
    await callback.answer()

@dp.callback_query(F.data == "back_to_amount")
async def back_to_amount(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Валюта", callback_data="choose_currency")],
        [InlineKeyboardButton(text="Назад", callback_data="create_deal")]
    ])
    await send_screen(callback.message.chat.id, "choose_amount", kb, edit_message=callback.message)
    await state.set_state(DealStates.entering_amount)
    await callback.answer()

@dp.message(DealStates.entering_nft_link)
async def process_nft_link(message: types.Message, state: FSMContext):
    nft_link = message.text
    if "t.me/nft/" not in nft_link:
        await message.answer("Отправьте корректную ссылку на NFT (t.me/nft/...).")
        return

    data = await state.get_data()
    amount = data.get("amount")
    currency = data.get("currency")
    method = data.get("payment_method")
    
    deal_id_raw = generate_deal_id()
    deal_id = deal_id_raw.replace("#", "")
    
    deal_data = {
        "deal_id": deal_id_raw,
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "amount": amount,
        "currency": currency,
        "nft_link": nft_link,
        "details": f"Ожидание реквизитов ({method})",
        "status": "Ожидает оплаты",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    deals = get_deals()
    deals.append(deal_data)
    save_deals(deals)
    await state.clear()

    bot_info = await bot.get_me()
    deal_link = f"https://t.me/{bot_info.username}?start={deal_id}"

    success_text = (
        f"Сделка {deal_id_raw} успешно создана!\n\n"
        f"Получение оплаты: {currency}\n"
        f"Сумма: {amount}\n\n"
        f"подарки:\n"
        f"<code>{nft_link}</code>\n\n"
        f"Ссылка для покупателя:\n"
        f"{deal_link}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить сделку", callback_data=f"cancel_deal_{deal_id}")]
    ])
    
    # Проверяем, есть ли сохраненная картинка для экрана успеха
    success_photo = get_image("deal_success")
    if success_photo:
        await message.answer_photo(photo=success_photo, caption=success_text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(success_text, reply_markup=kb, parse_mode="HTML")

# --- ОТМЕНА СДЕЛКИ ---
@dp.callback_query(F.data.startswith("cancel_deal_"))
async def cancel_deal(callback: types.CallbackQuery):
    deal_id = callback.data.replace("cancel_deal_", "")
    update_deal_status(deal_id, "Отменена")
    await callback.message.edit_text(f"Сделка {deal_id} отменена.", parse_mode="HTML")
    await callback.answer()

# --- АДМИН ПАНЕЛЬ (Команда /ruvire) ---
@dp.message(Command("ruvire"))
async def cmd_admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("У вас нет доступа.")

    menu_text = (
        "<b>Настройка бота</b>\n\n"
        "Выберите номер того, что хотите изменить (отправьте цифру):\n\n"
        "1. Текст приветствия (Главное меню)\n"
        "2. Текст выбора метода оплаты\n"
        "3. Текст ввода суммы\n"
        "4. Текст выбора валюты\n"
        "5. Текст ввода ссылки на NFT\n"
        "6. Текст экрана успешной сделки\n"
        "7. Картинка: Главное меню\n"
        "8. Картинка: Выбор метода оплаты\n"
        "9. Картинка: Ввод суммы\n"
        "10. Картинка: Выбор валюты\n"
        "11. Картинка: Ввод ссылки на NFT\n"
        "12. Картинка: Экран успешной сделки\n"
        "13. Добавить админа\n"
        "14. Удалить админа\n\n"
        "После отправки цифры, отправьте новый текст или картинку."
    )
    await message.answer(menu_text, parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_choice)

@dp.message(AdminStates.waiting_for_choice)
async def process_admin_choice(message: types.Message, state: FSMContext):
    choice = message.text
    if not choice.isdigit():
        return await message.answer("Отправьте число.")
    
    choice = int(choice)
    if choice < 1 or choice > 14:
        return await message.answer("Неверный номер.")
        
    # Сопоставление номеров и ключей
    keys_map = {
        1: "welcome", 2: "choose_method", 3: "choose_amount", 4: "choose_currency", 5: "enter_nft", 6: "deal_success",
        7: "welcome", 8: "choose_method", 9: "choose_amount", 10: "choose_currency", 11: "enter_nft", 12: "deal_success"
    }
    
    if choice in [13, 14]:
        # Логика добавления/удаления админов (для краткости показываю добавление)
        if choice == 13:
            await message.answer("Отправьте ID пользователя, которого хотите сделать админом:")
            await state.set_state(AdminStates.waiting_for_new_value)
            await state.update_data(action="add_admin")
            return
        else:
            await message.answer("Логика удаления админов (можно добавить по аналогии)")
            await state.clear()
            return
            
    key = keys_map[choice]
    action = "image" if choice >= 7 else "text"
    
    await state.update_data(key=key, action=action)
    await message.answer(f"Отправьте новое значение для пункта {choice}:")
    await state.set_state(AdminStates.waiting_for_new_value)

@dp.message(AdminStates.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    key = data.get("key")
    
    settings = get_settings()
    
    if action == "add_admin":
        try:
            new_id = int(message.text)
            if new_id not in settings["admins"]:
                settings["admins"].append(new_id)
                save_settings(settings)
                await message.answer(f"Пользователь {new_id} добавлен в админы.")
            else:
                await message.answer("Он уже админ.")
        except:
            await message.answer("Ошибка. Отправьте ID цифрами.")
        await state.clear()
        return
        
    if action == "text":
        if key not in settings["texts"]:
            settings["texts"][key] = ""
        settings["texts"][key] = message.html_text
        save_settings(settings)
        await message.answer("Текст обновлен.")
    
    elif action == "image":
        if not message.photo:
            await message.answer("Вы должны отправить картинку.")
            return
        if "images" not in settings:
            settings["images"] = {}
        settings["images"][key] = message.photo[-1].file_id
        save_settings(settings)
        await message.answer("Картинка обновлена.")
        
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
