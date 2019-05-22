import telebot
from telebot import types
import requests
import os
import json
from collections import defaultdict
import geopy.distance


token = '746155048:AAGeC6EMFDgKPqb9ed1GCZCIY9xQm-UouH4'
START, ADDR, COORD, PHOTO, SAVE, NEARBY, SEND = range(7)

USER_STATE = defaultdict(lambda: START)
PLACES = defaultdict(lambda: {})
base = os.getcwd()
photo_dir = os.path.join(base,'storage')#'C:\\tele_bot\\storage\\'
db = os.path.join(base,'storage','db')#'C:\\tele_bot\\storage\\db'
but1 = ['Помощь', 'Добавить', 'Все', '10', 'Удалить']
but2 = ['Помощь', 'Добавить', '10', 'Все']
but3 = ['Помощь', 'Добавить']
bot = telebot.TeleBot(token)

def create_keyboard1():
    keyboard1 = types.InlineKeyboardMarkup(row_width=3)
    buttons1 = [types.InlineKeyboardButton(text=b, callback_data=b) for b in but1]
    keyboard1.add(*buttons1)
    return keyboard1

def create_keyboard2():
    keyboard2 = types.InlineKeyboardMarkup(row_width=2)
    buttons2 = [types.InlineKeyboardButton(text=b, callback_data=b) for b in but2]
    keyboard2.add(*buttons2)
    return keyboard2

def create_keyboard3():
    keyboard3 = types.InlineKeyboardMarkup(row_width=2)
    buttons3 = [types.InlineKeyboardButton(text=b, callback_data=b) for b in but3]
    keyboard3.add(*buttons3)
    return keyboard3

def get_state(message):
    return USER_STATE[message.chat.id]

def update_state(message, state):
    USER_STATE[message.chat.id] = state

def update_locations(user_id, key, value):
    PLACES[user_id][key] = value


def read_txt_db():
    try:
        with open(db, 'r') as rf:
            content = json.load(rf)
    except json.decoder.JSONDecodeError:
        content = {}
    return content

def update_db(user_id):
    content = read_txt_db()
    if content.get(str(user_id)):
        seq_list = []
        for entry in content[str(user_id)]:
            seq_list.append(entry['seq'])
        seq =  max(seq_list) + 1
    else:
        seq = 1
        content[str(user_id)] = []
    update_locations(user_id, 'seq', seq)
    content[str(user_id)].append(PLACES[user_id])
    #print('end', content)
    with open(db, 'w') as wa:
        json.dump(content,wa)

def view_loc(user_id):
    content = read_txt_db()
    msg = ''
    if content.get(str(user_id)):
        for entry in content[str(user_id)]:
            msg += str(entry['seq']) + '. ' + entry['address'] + ' (' + str(round(entry['coordinates'][0], 2)) + ',' +\
                   str(round(entry['coordinates'][1], 2)) + ')' + '\n'
    return msg

def view_10loc(user_id):
    content = read_txt_db()
    msg = ''
    if content.get(str(user_id)):
        l = len(content.get(str(user_id)))
        #if l > 10:
        for entry in content[str(user_id)]:
            if entry['seq'] in range(l-10, l+1):
                msg += str(entry['seq']) + '. ' + entry['address'] + ' (' + str(round(entry['coordinates'][0], 2)) +\
                           ',' + str(round(entry['coordinates'][1], 2)) + ')' + '\n'
    return msg

def calc_distance(user_id,lat, lon):
    content = read_txt_db()
    msg = ''
    if content.get(str(user_id)):
        for entry in content[str(user_id)]:
            center = (lat, lon)
            dist = round(geopy.distance.vincenty(center, tuple(entry['coordinates'])).m, 2)
            if dist <= 500:
                msg += entry['address'] + ': ' + str(dist) + ' м\n'
    else:
        msg = 'Вы не добавили еще не одной локации'
    return msg

def delete_user_loc(user_id):
    content = read_txt_db()
    if content.get(str(user_id)):
        content[str(user_id)] = []
        with open(db, 'w') as wa:
            json.dump(content, wa)

#========================================
#========================================
@bot.message_handler(commands=['start'])
def handle_grit(message):
    keyboard1 = create_keyboard1()
    bot.send_message(chat_id=message.chat.id, text='Привет, я бот, который запоминает посещенные места. '
                                                   'Для добавления места наберите команду /add.'
                                                   'Для просмотра сохраненых мест дайте команду /list. '                                                   
                                                   'Для просмотра последних добавленных 10 мест выполните /last. '
                                                   'Для удаления всех мест наберите /reset. '
                                                   'Просто отправьте локацию, чтобы увидеть сохраненные места в радиусе 500 метров'
                                                   ' или нажимайте на кнопки', reply_markup=keyboard1)
    update_state(message, START)

@bot.message_handler(commands=['add'])
def handle_start(message):
    bot.send_message(chat_id=message.chat.id, text='Введите адрес места ➕')
    update_state(message, ADDR)

@bot.message_handler(func=lambda message: get_state(message) == ADDR)
def handle_address(message):
    update_locations(message.chat.id, 'address', message.text)
    bot.send_message(chat_id=message.chat.id, text='Введите координаты места через запятую или отправьте свое местоположение')
    update_state(message, COORD)

@bot.message_handler(func=lambda message: get_state(message) == COORD)
def handle_coord(message):
    try:
        co = message.text.split(',')
        lat, lon = float(co[0]), float(co[1])
        update_locations(message.chat.id, 'coordinates', (lat, lon))
        bot.send_message(chat_id=message.chat.id, text='Сделайте фото, если хотите, иначе введите "нет"')
        update_state(message, PHOTO)
    except:
        bot.send_message(chat_id=message.chat.id, text='Введите верные координаты: два числа через запятую')

@bot.message_handler(content_types=['location'])
def handle_photo(message):
    if get_state(message) == COORD:
        if message.location is not None:
            update_locations(message.chat.id, 'coordinates', (message.location.latitude, message.location.longitude))
            bot.send_message(chat_id=message.chat.id,
                            text='Сделайте фото, если хотите, иначе введите "нет"')
            update_state(message, PHOTO)
    else:
            #get_state(message) == SEND:
        keyboard1 = create_keyboard1()
        if message.location is not None:
            bot.send_message(chat_id=message.chat.id, text='Расстояния до сохраненных локаций в радиусе 500 метров 🚶 :')
            msg = calc_distance(message.chat.id, message.location.latitude, message.location.longitude)
            if msg != '':
                bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard1)
            else:
                bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации')
        update_state(message, START)


@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
@bot.message_handler(content_types=['photo'])
def handle_save(message):
    keyboard1 = create_keyboard1()
    if message.text is None:
        try:
            file = bot.get_file(message.photo[-1].file_id)
            requested_file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(token, file.file_path))
            print('photo_dir, foto_file', photo_dir,file.file_path)
            print('db', db)
            with open(os.path.join(photo_dir,file.file_path), 'wb') as f:
                f.write(requested_file.content)
            update_state(message, SAVE)
            update_locations(message.chat.id, 'photo', os.path.join(photo_dir,file.file_path))
            update_db(message.chat.id)
            bot.send_message(chat_id=message.chat.id, text='Место сохранено', reply_markup=keyboard1)
        except:
            bot.send_message(chat_id=message.chat.id, text='Фотографии не обнаружено, сделайте фотографию или напишите нет')
    else:
        if message.text.lower() == 'нет':
            update_locations(message.chat.id, 'photo', '')
            update_state(message, SAVE)
            update_db(message.chat.id)
            bot.send_message(chat_id=message.chat.id, text='Место сохранено', reply_markup=keyboard1)
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Фотографии не обнаружено, сделайте фотографию или напишите нет (в любом регистре)')
#=================================
#=================================
@bot.message_handler(commands=['list'])
def handle_list(message):
    keyboard2 = create_keyboard2()
    bot.send_message(chat_id=message.chat.id, text='Ранее сохраненные локации 🏡 :')
    vl = view_loc(message.chat.id)
    if vl != '':
        bot.send_message(chat_id=message.chat.id, text=vl, reply_markup=keyboard2)
    else:
        bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации')
#=================================
#=================================
@bot.message_handler(commands=['last'])
def handle_list(message):
    keyboard2 = create_keyboard2()
    bot.send_message(chat_id=message.chat.id, text='Последние сохраненные 10 локаций 🏡 :')
    vl = view_10loc(message.chat.id)
    if vl != '':
        bot.send_message(chat_id=message.chat.id, text=vl, reply_markup=keyboard2)
    else:
        bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации')
#=================================
#=================================
@bot.message_handler(commands=['reset'])
def handle_reset(message):
    keyboard3 = create_keyboard3()
    delete_user_loc(message.chat.id)
    bot.send_message(chat_id=message.chat.id, text='Сохраненные локации удалены 🐒', reply_markup=keyboard3)
#=================================
#=================================
@bot.message_handler(commands=['nearby'])
def handle_nearby(message):
    keyboard1 = create_keyboard3()
    bot.send_message(chat_id=message.chat.id, text='Пришлите свою локацию', reply_markup=keyboard1)
    update_state(message, SEND)
#================================
#================================
@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    message = callback_query.message
    text = callback_query.data
    if text == 'Удалить':
        keyboard3 = create_keyboard3()
        delete_user_loc(message.chat.id)
        bot.send_message(chat_id=message.chat.id, text='Сохраненные локации удалены 🐒', reply_markup=keyboard3)
        #bot.answer_callback_query(callback_query.id, text='Сохраненные локации удалены', reply_markup=keyboard3)
    elif text == 'Все':
        keyboard1 = create_keyboard1()
        bot.answer_callback_query(callback_query.id, text='Ранее сохраненные локации:')
        #view_loc(message.chat.id)
        if view_loc(message.chat.id) != '':
            bot.send_message(chat_id=message.chat.id, text=view_loc(message.chat.id), reply_markup=keyboard1)
        else:
            bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации', reply_markup=keyboard1)
    elif text == '10':
        keyboard1 = create_keyboard1()
        bot.answer_callback_query(callback_query.id, text='Последние сохраненные 10 локаций:')
        #view_loc(message.chat.id)
        if view_loc(message.chat.id) != '':
            bot.send_message(chat_id=message.chat.id, text=view_10loc(message.chat.id), reply_markup=keyboard1)
        else:
            bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации', reply_markup=keyboard1)
    #elif text == '500':
    #    bot.send_message(chat_id=message.chat.id, text='Пришлите свою локацию')
    #    update_state(message, SEND)
        #bot.answer_callback_query(callback_query.id, text='Пришлите свою локацию')
    elif text == 'Добавить':
        bot.send_message(chat_id=message.chat.id, text='Введите адрес места')
        update_state(message, ADDR)
        #bot.answer_callback_query(callback_query.id, text='Пришлите свою локацию')
    elif text == 'Помощь':
        keyboard1 = create_keyboard1()
        bot.send_message(chat_id=message.chat.id, text='Привет, я бот, который запоминает посещенные места. '
                                                   'Для добавления места наберите команду /add.'
                                                   'Для просмотра сохраненых мест дайте команду /list. '                                                   
                                                   'Для просмотра последних добавленных 10 мест выполните /last. '
                                                   'Для удаления всех мест наберите /reset. '
                                                   'Просто отправьте локацию, чтобы увидеть сохраненные места в радиусе 500 метров'
                                                   ' или нажимайте на кнопки', reply_markup=keyboard1)

bot.polling()

