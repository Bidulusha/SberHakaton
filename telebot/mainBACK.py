import telebot
import aiofiles
import os
import csv
import sys
from io import StringIO
from telebot import types
import asyncio

# INITIALIZED 
bot = telebot.TeleBot('7274811451:AAH9Xyd1vJNRRitZu4AHqZ40CWIBHeEfI8o')

actualfolder = 0
actualfile = 1
endOfImages = False

# CROPPED FOLDERS LIST
croppedfolderslist = os.listdir("../")

# STATE FILE
STATE_FILE = 'state.txt'

def create_reply_markup():
    """Создает постоянные кнопки под полем ввода"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item_start = types.KeyboardButton('/start')
    item_next = types.KeyboardButton('/next')
    item_cancel = types.KeyboardButton('/cancel')
    markup.add(item_start, item_next, item_cancel)
    return markup

async def load_state():
    """Загружает состояние из файла"""
    if not os.path.exists(STATE_FILE):
        return None
        
    async with aiofiles.open(STATE_FILE, 'r') as f:
        content = await f.read()
        lines = content.split('\n')
        if len(lines) >= 4:
            return {
                'actualfolder': int(lines[0].strip()),
                'actualfile': int(lines[1].strip()),
                'folder_path': lines[2].strip(),
                'endOfImages': lines[3].strip() == 'True'
            }
    return None

async def save_state(actualfolder, actualfile, folder_path, endOfImages):
    """Сохраняет состояние в файл"""
    async with aiofiles.open(STATE_FILE, 'w') as f:
        await f.write(f"{actualfolder}\n")
        await f.write(f"{actualfile}\n")
        await f.write(f"{folder_path}\n")
        await f.write(f"{endOfImages}\n")

async def initialize_state():
    """Инициализирует глобальное состояние"""
    global actualfolder, actualfile, folder_path, endOfImages
    
    saved_state = await load_state()
    if saved_state:
        actualfolder = saved_state['actualfolder']
        actualfile = saved_state['actualfile']
        folder_path = saved_state['folder_path']
        endOfImages = saved_state['endOfImages']

    while actualfolder < len(croppedfolderslist) and '.' in croppedfolderslist[actualfolder]:
        actualfolder += 1

    if actualfolder == len(croppedfolderslist):
        print("Where is nothing!")
        exit()

    folder_path = '../' + croppedfolderslist[actualfolder] + '/'

# COMMAND HANDLER
@bot.message_handler(content_types=['text'])
async def index(message):
    global actualfolder, actualfile, folder_path, endOfImages
    
    markup = create_reply_markup()
    await save_state(actualfolder, actualfile, folder_path, endOfImages)

    if endOfImages:
        await bot.send_message(message.from_user.id, text='ПОКА КАРТИНОК НЕТ')
        return 

    if message.text == '/cancel':
        await bot.send_message(message.from_user.id, 
                             text='Введите корректный текст,\n для отмены введите /next', 
                             reply_markup=markup)
        actualfile -= 1
        await bot.register_next_step_handler(message, getCorrectText)
    else:
        # Чтение CSV с помощью aiofiles
        async with aiofiles.open(folder_path + 'cropped.csv', 'r', encoding='utf-8') as f:
            content = await f.read()
            spamreader = list(csv.reader(StringIO(content), delimiter='\t', quotechar='|'))

        if message.text in ('/start', '/next'):
            if message.text == '/start':
                await bot.send_message(message.from_user.id, 
                                    text='Привет, тебе предстоит смотреть на картиночки и править текст на картиночках!\
                                    \nЯ дам тебе картиночку а ты должен будешь проверить правильный ли я текст нашаманил.\
                                    \nЕсли же он неправильный то прошу помоги мне его исправить!\
                                    \nСмотри, если ты ввёл текст, но потом заметил что и сам ошибся введи /cancel', 
                                    reply_markup=markup)

            # GET IMAGE AND TEXT
            imagename, text = spamreader[actualfile]
            image = open(folder_path + imagename, 'rb')

            # KEYBOARD
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_yes, key_no)

            await bot.send_photo(message.from_user.id, photo=image)
            await bot.send_message(message.from_user.id,
                                 text='Текст на картинке:\n' + text,
                                 reply_markup=keyboard)
        else:
            await bot.send_message(message.from_user.id, text='Ошибка в команде!')

# BUTTONS
@bot.callback_query_handler(func=lambda call: True)
async def callback_worker(call):
    global actualfolder, actualfile, folder_path, endOfImages

    if call.data == 'yes':
        actualfile += 1
        # Создаем fake message с /next
        msg = types.Message(
            message_id=call.message.message_id + 1,
            from_user=call.from_user,
            date=call.message.date,
            chat=call.message.chat,
            content_type='text',
            json_string='{"text": "/next"}'
        )
        await index(msg)
    elif call.data == 'no':
        await bot.send_message(call.message.chat.id, 
                             text='Введите корректный текст,\nдля отмены введите /next')
        await bot.register_next_step_handler(call.message, getCorrectText)

# UPDATE ACTUAL FOLDER
def updateActualFolder():
    global actualfolder, actualfile, folder_path, endOfImages

    while actualfolder < len(croppedfolderslist) and '.' in croppedfolderslist[actualfolder]:
        actualfolder += 1

    if actualfolder == len(croppedfolderslist):
        endOfImages = True

# GET CORRECT TEXT AND ADD IT TO CSV
async def getCorrectText(message):
    global actualfolder, actualfile, folder_path

    # Чтение CSV
    async with aiofiles.open(folder_path + 'cropped.csv', 'r', encoding='utf-8') as f:
        content = await f.read()
        rows = list(csv.reader(StringIO(content), delimiter='\t', quotechar='|'))

    if message.text == '/next':
        actualfile += 1
        if actualfile == len(rows):
            actualfile = 1
            updateActualFolder()
    else:
        rows[actualfile][1] = message.text

    # Запись CSV
    output = StringIO()
    writer = csv.writer(output, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerows(rows)
    
    async with aiofiles.open(folder_path + 'cropped.csv', 'w', encoding='utf-8') as f:
        await f.write(output.getvalue())

    actualfile += 1
    if actualfile == len(rows):
        actualfile = 1
        updateActualFolder()

    # Создаем fake message с /next
    msg = types.Message(
        message_id=message.message_id + 1,
        from_user=message.from_user,
        date=message.date,
        chat=message.chat,
        content_type='text',
        json_string='{"text": "/next"}'
    )
    await index(msg)

# Запуск инициализации состояния
async def main():
    await initialize_state()
    bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    asyncio.run(main())