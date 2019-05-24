import telebot
from telebot import types
import requests
import os
import json
from collections import defaultdict
import geopy.distance


token = '746155048:AAGeC6EMFDgKPqb9ed1GCZCIY9xQm-UouH4'

START, ADDR, COORD, PHOTO, SAVE, NEARBY, SEND = range(7)
UNLOCK, LOCK = range(2)
USER_STATE = defaultdict(lambda: START)
LOCK_LOC = defaultdict(lambda: UNLOCK)
PLACES = defaultdict(lambda: {})
base = os.getcwd()
photo_dir = os.path.join(base,'storage')#'C:\\tele_bot\\storage\\'
db = os.path.join(base,'storage','db')#'C:\\tele_bot\\storage\\db'

but1 = ['Помощь', 'Добавить', 'Список', 'Последние', 'Удалить']
but2 = ['Помощь', 'Добавить', 'Последние', 'Список']
but3 = ['Помощь', 'Добавить']
bot = telebot.TeleBot(token)
# print(bot.get_me())


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


def get_lock(message):
    return LOCK_LOC[message.chat.id]


def update_lock(message, state):
    LOCK_LOC[message.chat.id] = state


def update_locations(user_id, key, value):
    PLACES[user_id][key] = value


def read_txt_db():
    try:
        with open(db, 'r') as rf:
            content = json.load(rf)
    except json.decoder.JSONDecodeError:
        content = {}
    return content


def get_sequence(user_id, content):
    if content.get(str(user_id)):
        seq_list = []
        for entry in content[str(user_id)]:
            seq_list.append(entry['seq'])
        seq =  max(seq_list) + 1
    else:
        seq = 1
    return seq


def update_db(user_id, content):
    seq = get_sequence(user_id, content)
    if seq == 1:
        content[str(user_id)] = []
    update_locations(user_id, 'seq', seq)
    content[str(user_id)].append(PLACES[user_id])
    # print('end', content)
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


def get_last10_num(user_id, content):
    seq_list = []
    if content.get(str(user_id)):
        l = len(content.get(str(user_id)))
        for entry in content[str(user_id)]:
            if entry['seq'] in range(l-11, l+1):
                seq_list.append(str(entry['seq']))
    return seq_list


def view_10loc(user_id):
    content = read_txt_db()
    msg = ''
    if content.get(str(user_id)):
        l = len(content.get(str(user_id)))
        for entry in content[str(user_id)]:
            if entry['seq'] in range(l-11, l+1):
                msg += str(entry['seq']) + '. ' + entry['address'] + ' (' + str(round(entry['coordinates'][0], 2)) +\
                           ',' + str(round(entry['coordinates'][1], 2)) + ')' + '\n'
    return msg


def get_one_loc(user_id, content, seq):
    if content.get(str(user_id)):
        entry = list(filter(lambda x: x['seq'] == seq, content[str(user_id)]))[0]
        return entry['address'], entry['photo']


def calc_distance(user_id,lat, lon):
    content = read_txt_db()
    print(user_id, content)
    msg = ''
    if content.get(str(user_id)):
        for entry in content[str(user_id)]:
            center = (lat, lon)
            dist = round(geopy.distance.vincenty(center, tuple(entry['coordinates'])).m, 2)
            if dist <= 500:
                msg += entry['address'] + ': ' + str(dist) + ' м\n'
        if msg == '':
            msg = 'В радиусе 500 метров нет сохраненных локаций'
    else:
        msg = 'Вы не добавили еще не одной локации'
    return msg


def delete_user_loc(user_id):
    content = read_txt_db()
    if content.get(str(user_id)):
        content[str(user_id)] = []
        with open(db, 'w') as wa:
            json.dump(content, wa)

# ========================================
# ========================================


@bot.message_handler(commands=['start'])
def handle_grit(message):
    keyboard1 = create_keyboard1()
    update_lock(message, UNLOCK)
    bot.send_message(chat_id=message.chat.id, text='Привет, я бот, который запоминает посещенные места. '
                                                   'Для добавления места наберите команду /add.'
                                                   'Для просмотра сохраненых мест дайте команду /list. '                                                   
                                                   'Для просмотра последних добавленных 10 мест выполните /last. '
                                                   'Для удаления всех мест наберите /reset. '
                                                   'Просто отправьте локацию, чтобы увидеть сохраненные места в радиусе'
                                                   ' 500 метров или нажимайте на кнопки', reply_markup=keyboard1)
    update_state(message, START)


@bot.message_handler(func=lambda message: get_state(message) == START)
@bot.message_handler(commands=['add'])
def handle_start(message):
    update_lock(message, LOCK)
    bot.send_message(chat_id=message.chat.id, text='Введите адрес места ➕')
    update_state(message, ADDR)


@bot.message_handler(func=lambda message: get_state(message) == ADDR)
def handle_address(message):
    if isinstance(message.text,str):
        update_locations(message.chat.id, 'address', message.text)
        bot.send_message(chat_id=message.chat.id, text='Введите координаты места через запятую '
                                                   'или отправьте свое местоположение')
        update_state(message, COORD)
    else:
        bot.send_message(chat_id=message.chat.id, text='Вы ввели не текстовое сообщение,'
                                                       'напишите название места')
        update_state(message, START)


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
    state = get_state(message)
    keyboard1 = create_keyboard1()
    if state == COORD:
        if message.location is not None:
            update_locations(message.chat.id, 'coordinates', (message.location.latitude, message.location.longitude))
            bot.send_message(chat_id=message.chat.id,
                            text='Сделайте фото, если хотите, иначе введите "нет"')
            update_state(message, PHOTO)
    elif get_lock(message) == UNLOCK:
            # get_state(message) == SEND:

        if message.location is not None:
            bot.send_message(chat_id=message.chat.id, text='Расстояния до сохраненных локаций в радиусе 500 метров 🚶 :')

            msg = calc_distance(message.chat.id, message.location.latitude, message.location.longitude)
            print(msg)
            if msg != '':
                bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard1)
            else:
                bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации')
        update_state(message, START)
    else:
        bot.send_message(chat_id=message.chat.id, text='Получение локаций в радиусе 500 метров сейчас заблокировано,'
                                                       'нажмите кнопку "Помощь" или дайте команду /start '
                                                       'для разблокировки', reply_markup=keyboard1)


@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
@bot.message_handler(content_types=['photo'])
def handle_save(message):
    keyboard1 = create_keyboard1()
    content = read_txt_db()
    # seq = get_sequence(message.chat.id, content)
    if message.text is None and get_state(message) == PHOTO:
        try:
            file = bot.get_file(message.photo[-1].file_id)
            update_state(message, SAVE)
            update_locations(message.chat.id, 'photo', message.photo[-1].file_id)
            update_db(message.chat.id, content)
            bot.send_message(chat_id=message.chat.id, text='Место сохранено')
            bot.send_sticker(message.chat.id, "CAADAgADYAIAAgvNDgNERok1XlXTOQI", reply_markup=keyboard1)
            update_lock(message, UNLOCK)
        except:
            bot.send_message(chat_id=message.chat.id, text='Фотографии не обнаружено, сделайте фотографию '
                                                           'или напишите нет')
    elif message.text and get_state(message) == PHOTO:
        if message.text.lower() == 'нет':
            update_locations(message.chat.id, 'photo', '')
            update_state(message, SAVE)
            update_db(message.chat.id, content)
            update_lock(message, UNLOCK)
            bot.send_message(chat_id=message.chat.id, text='Место сохранено', reply_markup=keyboard1)
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Фотографии не обнаружено, сделайте фотографию или напишите нет (в любом регистре)')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Вы прислали просто изображение, для добавления локации,'
                              ' воспользуйтесь кнопкой "Добавить"', reply_markup=keyboard1)
# =================================
# =================================


@bot.message_handler(commands=['list'])
def handle_list(message):
    keyboard1 = create_keyboard1()
    if view_loc(message.chat.id):
        bot.send_message(chat_id=message.chat.id, text=view_loc(message.chat.id), reply_markup=keyboard1)
    else:
        bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации', reply_markup=keyboard1)


# --------------------------------
# --------------------------------
@bot.message_handler(commands=['last'])
def handle_list(message):
    content = read_txt_db()
    l = len(content[str(message.chat.id)])

    def create_keyboard10(user_id, content):
        but10 = []
        if len(content[str(user_id)]) >= 10:
            but10 = list(map(str, range(1, 11)))
        else:
            but10 = list(map(str, range(1, len(content[str(user_id)]) + 1)))
        but10.append('Обратно')
        keyboard10 = types.InlineKeyboardMarkup(row_width=len(but10))
        buttons10 = [types.InlineKeyboardButton(text=b, callback_data=b) for b in but10]
        keyboard10.add(*buttons10)
        return keyboard10

    if content.get(str(message.chat.id)):
        keyboard10 = create_keyboard10(message.chat.id, content)
        adr, foto = get_one_loc(message.chat.id, content, 1)
        if foto:
            bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
        else:
            bot.send_message(chat_id=message.chat.id, text=adr)
            bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    else:
        keyboard3 = create_keyboard3()
        bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации',
                         reply_markup=keyboard3)


@bot.message_handler(commands=['reset'])
def handle_reset(message):
    keyboard3 = create_keyboard3()
    delete_user_loc(message.chat.id)
    bot.send_message(chat_id=message.chat.id, text='Сохраненные локации удалены 🐒', reply_markup=keyboard3)


@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    def get_seq(content):
        l = len(content[str(message.chat.id)])
        if l > 10:
            return l - 11 + int(text)
        else:
            return int(text)

    def create_keyboard10(user_id, content):
        but10 = []
        if len(content[str(user_id)]) >= 10:
            but10 = list(map(str, range(1, 11)))
        else:
            but10 = list(map(str, range(1, len(content[str(user_id)]) + 1)))
        but10.append('Обратно')
        keyboard10 = types.InlineKeyboardMarkup(row_width=len(but10))
        buttons10 = [types.InlineKeyboardButton(text=b, callback_data=b) for b in but10]
        keyboard10.add(*buttons10)
        return keyboard10

    message = callback_query.message
    text = callback_query.data

    if text == 'Удалить':
        keyboard3 = create_keyboard3()
        delete_user_loc(message.chat.id)
        bot.send_sticker(message.chat.id, "CAADAgADYQIAAgvNDgPlVMLdWPpKoAI", reply_markup=keyboard3)
        bot.answer_callback_query(callback_query.id, text='Сохраненные локации удалены')
    elif text == 'Список':
        keyboard1 = create_keyboard1()
        bot.answer_callback_query(callback_query.id, text='Ранее сохраненные локации:')
        # view_loc(message.chat.id)
        if view_loc(message.chat.id):
            bot.send_message(chat_id=message.chat.id, text=view_loc(message.chat.id), reply_markup=keyboard1)
        else:
            bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации', reply_markup=keyboard1)

    elif text == 'Последние' or text == '1':
        content = read_txt_db()
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, 1)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
        else:
            keyboard3 = create_keyboard3()
            bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили не одной локации',
                             reply_markup=keyboard3)
    elif text == '2':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '3':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '4':
        content = read_txt_db()
        l = len(content[str(message.chat.id)])
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '5':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '6':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '7':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '8':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '9':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == '10':
        content = read_txt_db()
        seq = get_seq(content)
        if content.get(str(message.chat.id)):
            keyboard10 = create_keyboard10(message.chat.id, content)
            adr, foto = get_one_loc(message.chat.id, content, seq)
            if foto:
                bot.send_photo(chat_id=message.chat.id, caption=adr, photo=foto, reply_markup=keyboard10)
            else:
                bot.send_message(chat_id=message.chat.id, text=adr)
                bot.send_sticker(message.chat.id, "CAADAgADXwIAAgvNDgNx3DsRW3Y-UgI", reply_markup=keyboard10)
    elif text == 'Обратно':
        keyboard1 = create_keyboard1()
        bot.send_sticker(message.chat.id, "CAADAgADYAIAAgvNDgNERok1XlXTOQI", reply_markup=keyboard1)
    elif text == 'Добавить':
        update_lock(message, LOCK)
        bot.send_message(chat_id=message.chat.id, text='Введите адрес места')
        update_state(message, ADDR)
        # bot.answer_callback_query(callback_query.id, text='Пришлите свою локацию')
    elif text == 'Помощь':
        update_lock(message, UNLOCK)
        keyboard1 = create_keyboard1()
        bot.send_message(chat_id=message.chat.id, text='Привет, я бот, который запоминает посещенные места. '
                                                   'Для добавления места наберите команду /add.'
                                                   'Для просмотра сохраненых мест дайте команду /list. '                                                   
                                                   'Для просмотра последних добавленных 10 мест выполните /last. '
                                                   'Для удаления всех мест наберите /reset. '
                                                   'Просто отправьте локацию, чтобы увидеть сохраненные места в радиусе 500 метров'
                                                   ' или нажимайте на кнопки', reply_markup=keyboard1)

bot.polling()

