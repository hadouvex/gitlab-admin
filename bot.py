import os
import requests
import pathlib

from env import env

TOKEN = env['BOT_TOKEN']
URL_BASE = f'https://api.telegram.org/bot{TOKEN}/'

last_update_id = None

def send_message(chat_id, text='No message were recieved'):
    url = URL_BASE + f'sendmessage?chat_id={chat_id}&text={text}'
    requests.get(url)

def get_updates():
    url = URL_BASE + 'getupdates'
    response = requests.get(url)
    return response.json()

def get_last_message():
    data = get_updates()

    last_element = data['result'][-1]
    current_update_id = last_element['update_id']

    if last_update_id != current_update_id:
        global last_update_id
        last_update_id = current_update_id

        chat_id = last_element['message']['chat']['id']
        msg_text = last_element['message']['text']

        msg = {'chat_id': chat_id, 'msg_text': msg_text}

        return msg
    return None