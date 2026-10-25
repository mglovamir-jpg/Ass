import os
import requests
import threading
from time import localtime, strftime, time, sleep
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.common.by import By

# ===== ВВОД ДАННЫХ В КОНСОЛЬ =====
ACCESS_TOKEN = input('VK токен: ').strip()
GROUP_ID = int(input('ID группы: ').strip())
SCREEN_NAME = input('Домен: ').strip()
RPS = int(input('Запросов в секунду: ').strip())
BOT_TOKEN = input('Telegram bot token: ').strip()
CHAT_ID = input('Telegram chat id: ').strip()


def send_telegram(text):
    requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': text}
    )


session = requests.session()
claimed = False
refreshing = False
counter = 0
lock = threading.Lock()

PROFILE_DIR = os.path.abspath('chrome_profile')  # тут хранится логин в VK


def refresh_token():
    """Заходит на vkhost.github.io, выбирает vk.com, жмёт «Разрешить», забирает токен."""
    global ACCESS_TOKEN, refreshing
    with lock:
        if refreshing:
            return
        refreshing = True

    driver = None
    try:
        print('Обновляю токен через vkhost.github.io...')
        opts = webdriver.ChromeOptions()
        opts.add_argument(f'--user-data-dir={PROFILE_DIR}')
        driver = webdriver.Chrome(options=opts)
        driver.get('https://vkhost.github.io/')

        # выбор vk.com
        vk_xpath = "//*[contains(translate(normalize-space(text()),'VKCOM','vkcom'),'vk.com')]"
        for _ in range(60):
            try:
                driver.find_element(By.XPATH, vk_xpath).click()
                break
            except Exception:
                sleep(0.5)

        sleep(1)
        driver.switch_to.window(driver.window_handles[-1])

        # ждём страницу авторизации, жмём «Разрешить», ловим токен из адреса
        allow_xpath = "//button[contains(.,'Разрешить')] | //input[@value='Разрешить']"
        end = time() + 300
        while time() < end:
            url = driver.current_url
            if 'access_token=' in url:
                ACCESS_TOKEN = parse_qs(urlparse(url).fragment)['access_token'][0]
                print('Новый токен получен')
                break
            try:
                driver.find_element(By.XPATH, allow_xpath).click()
            except Exception:
                pass
            sleep(0.5)
    except Exception as e:
        print('Ошибка обновления токена:', e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        with lock:
            refreshing = False


def attempt():
    global claimed, counter
    try:
        with lock:
            counter += 1
            n = counter

        data = session.get(
            'https://api.vk.com/method/groups.edit',
            params={
                'access_token': ACCESS_TOKEN,
                'group_id': GROUP_ID,
                'screen_name': SCREEN_NAME,
                'v': 5.192
            }
        ).json()

        now = strftime("%H:%M:%S", localtime())

        # ===== УСПЕХ =====
        if 'response' in data:
            with lock:
                if claimed:
                    return
                claimed = True

            print(f'{now} [{n}] Domain Claimed! {SCREEN_NAME} -> {GROUP_ID}')

            send_telegram(
                f'Domain Claimed!\n'
                f'Домен: {SCREEN_NAME}\n'
                f'Попытки: {n}\n'
                f'Группа: {GROUP_ID}'
            )

        # ===== ТОКЕН НЕВАЛИДЕН =====
        elif data.get('error', {}).get('error_code') == 5:
            print(f'{now} [{n}] invalid access token')
            threading.Thread(target=refresh_token, daemon=True).start()

        else:
            print(f'{now} [{n}] zZz')

    except Exception as e:
        print('Ошибка:', e)


interval = 1 / RPS
next_shot = time()

while not claimed:
    threading.Thread(target=attempt).start()
    next_shot += interval
    pause = next_shot - time()
    if pause > 0:
        sleep(pause)
