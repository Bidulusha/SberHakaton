# TELEBOT
from telebot.async_telebot import AsyncTeleBot
from telebot import types
# ASYNC
import asyncio
import aiofiles
import aiocsv
from io import BytesIO
from io import StringIO
# OTHER
from PIL import Image
import os
import csv

class CheckBot:

    '''CONSTRUCTOR'''
    def __init__(self, token, croppedFoldersPath): 
        self.__bot = AsyncTeleBot(token)

        # INITIALIZE VARIABLES
        self.__actualFolder = 0
        self.__actualFile = -1
        self.__endOfImages = False
        self.__pressCancel = False

        self.__STATE_FILE = 'state.txt'
        self.__CreateReplyMarkup() # __replyMarkup

        self.__userInfo = {}

        self.__croppedFoldersList = os.listdir(croppedFoldersPath)
        self.__croppedFolderPath = croppedFoldersPath

        self.__InitializeState()

        self.__RegisterHandlers()


    '''INITIALIZATION FUNCTION'''
    # CREATE REPLY MARKUP
    def __CreateReplyMarkup(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        item_start = types.KeyboardButton('/start')
        item_next = types.KeyboardButton('/next')
        item_cancel = types.KeyboardButton('/cancel')
        
        markup.add(item_start, item_next, item_cancel)
        
        self.__replyMarkup = markup
    
    # INITIALIZE STATE
    def __InitializeState(self):
        self.__LoadState()

        while self.__actualFile < len(self.__croppedFoldersList) and '.' in self.__croppedFoldersList[self.__actualFolder]:
            self.__actualFolder += 1
        
        if self.__actualFolder == len(self.__croppedFoldersList):
            print('Where is nothing!')
            exit()

        self.__folderPath = self.__croppedFolderPath + self.__croppedFoldersList[self.__actualFolder] + '/'

    '''STATE FUNCTIONS'''
    # LOAD
    def __LoadState(self):
        if not os.path.exists(self.__STATE_FILE):
            return

        with open(self.__STATE_FILE, 'r') as csvfile:
            content = csvfile.read()
            lines = content.split('\n')


            self.__actualFolder = int(lines[0])
            self.__actualFile = int(lines[1])
            self.__folderPath = str(lines[2].strip())
            self.__endOfImages = str(lines[3].strip()) == 'True'


    # SAVE
    async def __SaveState(self):
        async with aiofiles.open(self.__STATE_FILE, 'w') as csvfile:
            await csvfile.write(f"{self.__actualFolder}\n")
            await csvfile.write(f"{self.__actualFile}\n")
            await csvfile.write(f"{self.__folderPath}\n")
            await csvfile.write(f"{self.__endOfImages}\n")



    '''MAIN BOT FUNCTIONS'''
    #COMMAND HandlerR
    def __RegisterHandlers(self):
        # COMMANDS
        @self.__bot.message_handler(commands=['start'])
        async def HandlerStart(message):
            await self.__HandlerStart(message)
        
        @self.__bot.message_handler(commands=['save'])
        async def HandlerSave(message):
            await self.__SetCSVFile()
            await self.__SaveState()

        @self.__bot.message_handler(commands=['next'])
        async def HandlerNext(message):
            await self.__HandlerNext(message)

        @self.__bot.message_handler(commands=['cancel'])
        async def HandlerCancel(message):
            await self.__HandlerNext(message, False)

        # BUTTONS
        @self.__bot.callback_query_handler(func=lambda call: True)
        async def ButtonWorker(call):
            message = call.message

            if call.data == 'yes':
                await self.__HandlerNext(message) 

            elif call.data == 'no':
                self.__tempActualFile = self.__actualFile
                await self.__bot.send_message(
                    message.chat.id,
                    text='Введите корректный текст,\nдля отмены введите /cancel'
                )

            else:
                await self.__bot.send_message(
                    message.chat.id,
                    text='Иди под струёй мойся'
                )
                return     

        # NO ONE COMMAND
        @self.__bot.message_handler(func=lambda message: True)  # Ловит ВСЕ сообщения
        async def HandlerUnknown(message):
            if self.__userstate in ['waiting for text']:  # ПЕРЕДЕЛАТЬ
                self.__GetCorrectText(message)
                await self.__HandlerNext(message, False) 

            else:
                await self.__bot.reply_to(message, "Извините, я не понимаю эту команду 卐\n"
                                                "Попробуйте /start, /next или /cancel")

            
        # AND ELSE
    
    '''COMMANDS'''
    #START
    async def __HandlerStart(self, message):
        await self.__bot.send_message(
            message.chat.id,
            text='Привет, тебе предстоит смотреть на картиночки и править текст на картиночках!\
                    \nЯ дам тебе картиночку а ты должен будешь проверить правильный ли я текст нашаманил.\
                    \nЕсли же он неправильный то прошу помоги мне его исправить!\
                    \nСмотри, если ты ввёл текст, но потом заметил что и сам ошибся введи /cancel\
                    \nЧтобы начать введи /next', 
            reply_markup=self.__replyMarkup
        )
    
    #NEXT
    async def __HandlerNext(self, message, next = True):

        if next:
            self.__MoveActualFile()
            if message.char.id in self.__userInfo:
                self.__userInfo[message.chat.id]['last'] = self.__userInfo[message.chat.id]['actual']
                self.__userInfo[message.chat.id]['actural'] = self.__actualFile
            else:
                self.__userInfo[message.chat.id]['actual'] = self.__userInfo[message.chat.id]['last'] = self.__actualFile


        photo = await self.__GetImage(message)
        await self.__bot.send_photo(
            message.chat.id,
            photo=photo
        )

        # ADD KEYBOARD
        keyboard = types.InlineKeyboardMarkup()

        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')

        keyboard.add(key_yes, key_no)
            

        await self.__bot.send_message(
            message.chat.id,
            text='Текст на картинке:\n' + self.__imagesDict[self.__userInfo[message.chat.id]['actual']]['text'],
            reply_markup=keyboard
        )

    #CANCEl
    async def __HandlerCancel(self, message):
        if self.__userstate == 'waiting for text': # ПЕРЕДЕЛАТь
            await self.__HandlerNext(message)
            return
        self.__userInfo = 'waiting for text'
        await self.__bot.send_message(
            message.chat.id,
            text='Повторите набор'
        )
            

    #GET CORRECT TEXT
    def __GetCorrectText(self, message):
        self.__imagesDict[self.__userInfo[message.chat.id]['actual']]['text'] = message.text


    '''FUNCTIONS'''
    #GET CSV
    async def __GetCSVFile(self):
        async with aiofiles.open(self.__folderPath + 'cropped.csv', 'r', newline='', encoding='utf-8') as csvfile:
            content = await csvfile.read()
            self.__imagesDict = list(csv.DictReader(StringIO(content), fieldnames=['filename', 'text'], delimiter='\t'))[1:]

        
    
    # SET CSV
    async def __SetCSVFile(self):
        async with aiofiles.open(self.__folderPath + 'cropped.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'text']

            writer = aiocsv.AsyncDictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
            await writer.writeheader()

            for image in self.__imagesDict:
                await writer.writerow(image)

    # MOVE ACTUAL FILE
    async def __MoveActualFile(self):
        if self.__actualFile < len(os.listdir(self.__folderPath)) - 1:
            self.__actualFile += 1
        else:
            self.__actualFile = 0
            while self.__actualFile < len(self.__croppedFoldersList) and '.' in self.__croppedFoldersList[self.__actualFolder]:
                self.__actualFolder += 1

            if self.__actualFile == len(self.__croppedFoldersList):
                self.__endOfImages = True
                return

            await self.__SetCSVFile()
            self.__folderPath = self.__croppedFolderPath + self.__croppedFoldersList[self.__actualFolder] + '/'
            await self.__GetCSVFile()

    #GET IMAGE
    async def __GetImage(self, message):
        filepath = self.__folderPath + self.__imagesDict[self.__userInfo[message.chat.id]['actual']]['filename']
        async with aiofiles.open(filepath, 'rb') as file:
            return await file.read()



    '''RUN BOT'''
    async def run(self):
        """Запуск бота"""
        await self.__GetCSVFile() # first init


        print("Бот запущен...")
        await self.__bot.infinity_polling()
        
        
    

    


        


        
        

