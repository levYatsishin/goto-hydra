import telebot
from telebot import types

from random import randint
from random import sample

import configparser
import json
import os
import shutil


main_dir = os.path.dirname(os.path.realpath(__file__))

# initializing config variables
config = configparser.ConfigParser()
config.read('config.ini')
token = config['VARS']['token']
admin_ids = config['VARS']['admin_ids'].split(', ')
start_command = config['VARS']['start_command']

bot = telebot.TeleBot(token)

prices_of_goods = {'Камень гашла  90гр': 170, 'Шмыга  14.5гр': 130, 'Сплиф  140гр': 125, 'Варево  300мл': 130}

# setting up markUps
markup_main = types.ReplyKeyboardMarkup(True)
markup_main.row('Товары','Счет')


markup_items = types.ReplyKeyboardMarkup(True)
for item in prices_of_goods.items():
    markup_items.row(f"{item[0]}")

markup_services = types.ReplyKeyboardMarkup(True)
markup_services.row('Заказать нападение')

markup_confirm = types.ReplyKeyboardMarkup(True)
markup_confirm.row('Да')
markup_confirm.row('Нет')


def send_place(message, item):
    item_raw = item
    item = item.split("  ")[0]

    if len(os.listdir(f'{main_dir}/Places/full/{item}/')) != 0:
        image_name = sample(os.listdir(f'{main_dir}/Places/full/{item}/'), len(os.listdir(f'{main_dir}/Places/full/{item}')))[0]

        while ".DS_Store" in image_name:
            image_name = sample(os.listdir(f'{main_dir}/Places/full/{item}/'),
                                len(os.listdir(f'{main_dir}/Places/full/{item}')))[0]

        image_path = f"{main_dir}/Places/full/{item}/{image_name}"

        with open(image_path, 'rb') as photo, \
                open(f"{main_dir}/Places/descriptions/{image_name.split('.')[0]}.txt", "r") as description_file:
            bot.send_photo(message.chat.id, photo)
            bot.send_message(message.chat.id, description_file.read())

        shutil.move(image_path, f'{main_dir}/Places/need_to_be_restored/{item}/{image_name}')

    else:
        edit_data(message, "money", int(read_data(message, id_=message.from_user.id, file="walet.json", value="money"))+prices_of_goods[item_raw], file="walet.json")
        bot.send_message(message.chat.id, f'К сожалению в данный мамент товар не в наличии, деньги вам возвращенны')


def message_to_admins(message):
    active = False
    if active:
        for admin in admin_ids:
            bot.send_message(admin, message, parse_mode='Markdown')


def transaction(thing_to_buy):
    # function which transfer goto_coins

    pass


def read_data(message, value,file='', id_=''):

    file_ = "data.json"

    if file != '':
        file_ = file
    with open(file_, "r+", encoding='utf8') as data_file:
        data = json.load(data_file)
        user_id = str(message.from_user.id)
        if id_ != '':
            user_id = str(id_)

        if user_id not in data.keys():
            return -1
        else:
            return data[user_id][value]


def edit_data(message, value, new_value, file='', id_=''):
    file_ = "data.json"

    if file != '':
        file_ = file
    with open(file_, "r+", encoding='utf8') as data_file:
        data = json.load(data_file)
        user_id = str(message.from_user.id)
        if id_ != '':
            user_id = str(id_)

        if user_id not in data.keys():
            new_data = {user_id: {value: new_value}}
            data.update(new_data)
            data_file.seek(0)
            json.dump(data, data_file, ensure_ascii=False)
        else:
            data[user_id][value] = new_value
            data_file.seek(0)
            data_file.truncate()
            json.dump(data, data_file, ensure_ascii=False)


def confirm(message):
    # function which is used to confirm any type of things (return 0/Сплиф(no/yes))
    item, price = read_data(message, value="buying_item")
    your_money = int(read_data(message, id_=message.from_user.id, file="walet.json", value="money"))
    if message.text is None:
        bot.send_message(message.chat.id, f'Вы уверенны что хотите купть *{item}* за *{price}*',
                         reply_markup=markup_confirm, parse_mode="Markdown")
        bot.register_next_step_handler(message, confirm)

    if (message.text.lower() == 'да') and your_money >= price:
        bot.send_message(message.chat.id, f"_Слот №{randint(10234, 504234)} успешно приобретен_\n\n"
                                          f"Вы купили *{item}* за *{price}*", reply_markup=markup_confirm,
                         parse_mode="Markdown")

        edit_data(message, id_=message.from_user.id, value="money",
                  new_value=your_money-price, file="walet.json")
        bot.send_message(message.chat.id, f'Ждите слейдующих инструкций',
                         reply_markup=markup_main)
        if item in prices_of_goods.keys():
            send_place(message, item)

    elif message.text.lower() == 'да':
        bot.send_message(message.chat.id, f'У вас: {your_money}\nСоит {price}', reply_markup=markup_items)
        bot.register_next_step_handler(message, goods)
        return 0

    elif message.text.lower() == 'нет':
        bot.send_message(message.chat.id, "Думайте, но вы можете не успеть", reply_markup=markup_main)

    else:
        bot.send_message(message.chat.id, f'Вы уверенны что хотите купть {item} за {price}',
                         reply_markup=markup_confirm)
        bot.register_next_step_handler(message, confirm)


def goods(message):
    # function which is used to buy goods

    if message.text is None:
        bot.send_message(message.chat.id, "Что Вы желаете приобрести?", parse_mode="Markdown")
        bot.register_next_step_handler(message, goods)
    elif message.text in prices_of_goods.keys():

        price = prices_of_goods[message.text]
        item = message.text

        edit_data(message, "buying_item", (item, price))
        bot.send_message(message.chat.id, f'Вы уверенны что хотите купть {item} за {price}',
                         reply_markup=markup_confirm)

        bot.register_next_step_handler(message, confirm)
    else:
        bot.send_message(message.chat.id, "Что Вы желаете приобрести?", parse_mode="Markdown")
        bot.register_next_step_handler(message, goods)


def services(message):
    # function which is used to buy services

    if message.text is None:
        bot.send_message(message.chat.id, "...", reply_markup=markup_services)
    elif message.text.lower() == "заказать нападение":
        bot.send_message(message.chat.id, "Цель для рассправы? \n_Формат Имя + Фамилия_", parse_mode="Markdown")
        bot.register_next_step_handler(message, assassin_service)


def assassin_service(message):
    # function which is used to buy services

    if message.text is None:
        bot.send_message(message.chat.id, "Цель для рассправы? \n_Формат Имя + Фамилия_", parse_mode="Markdown")
    else:
        if len(message.text.lower().split()) != 2:
            bot.send_message(message.chat.id, "Цель для рассправы? \n_Формат Имя + Фамилия_", parse_mode="Markdown")
            bot.register_next_step_handler(message, assassin_service)
            return 0

        price = randint(150, 250)
        item = f"Нападение на цель: {message.text.lower()}"

        edit_data(message, "buying_item", (item, price))
        bot.send_message(message.chat.id, f'Вы уверенны что хотите купть {item} за {price}',
                         reply_markup=markup_confirm)

        bot.register_next_step_handler(message, confirm)


@bot.message_handler(commands=['start'])
def start_message(message):
    # checking for registration
    code = message.text.split()[1] if len(message.text.split()) > 1 else None
    if code == start_command:
        with open("registered", "r+") as registered_file:
            registered_users = registered_file.read()
            if str(message.from_user.id) not in registered_users:
                edit_data(message, "money", 0, file="walet.json")
                registered_file.write(str(message.from_user.id) + "\n")

        bot.send_message(message.chat.id, "Здраствуй, путник", reply_markup=markup_main)


@bot.message_handler(commands=['list_of_orders', 'delete_order', 'add_money'])
def start_message(message):
    if str(message.from_user.id) in admin_ids:
        if message.text.lower() == '/list_of_orders':
            with open("data.json", "r+", encoding='utf8') as data_file:
                data = json.loads(data_file.read())
                bot.send_message(message.chat.id, str(data), reply_markup=markup_items)

        elif '/delete_order' in message.text.lower():
            bot.send_message(message.chat.id, message.text.lower().split(' ')[1], reply_markup=markup_items)

        elif '/add_money' in message.text.lower():
            bot.send_message(message.chat.id, "Got it", reply_markup=markup_items)
            edit_data(message, id_=message.text.lower().split(' ')[1], value="money", new_value=message.text.lower().split(' ')[2], file="walet.json")


@bot.message_handler(content_types=['text'])
def start_message(message):
    # checking for registration
    registered = False
    with open("registered", "r+", encoding='utf8') as registered_file:
        data = registered_file.read()
        if str(message.from_user.id) in data:
            registered = True

    if registered:
        if message.text.lower() == 'товары':
            bot.send_message(message.chat.id, "Что вы желаете преобрести?", reply_markup=markup_items)
            bot.register_next_step_handler(message, goods)
        elif message.text.lower() == 'счет':
            bot.send_message(message.chat.id, f"Ваш счет: {read_data(message, id_=message.from_user.id, file='walet.json', value='money')}", reply_markup=markup_items)

        else:
            bot.send_message(message.chat.id, "...", reply_markup=markup_main)


bot.polling()
