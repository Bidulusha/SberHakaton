import asyncio
import aiofiles
from io import StringIO

import checkbot

async def main():
    bot = checkbot.CheckBot('7274811451:AAH9Xyd1vJNRRitZu4AHqZ40CWIBHeEfI8o', 'cropped/')
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())