from tornado import ioloop
from tbot import tbot
from config import *
import logging
import os


bot = tbot.TelegramBot(db_creds={
                            'host': DB_HOST,
                            'database': DB_NAME,
                            'user': DB_USER,
                            'password': DB_PASSWORD,
                            'charset': 'utf8mb4'
                      },
                       token=ACCESS_TOKEN, vk_token=VK_TOKEN)

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'a').close()

LOG_LEVEL = 10
log = logging.getLogger('application')
log.setLevel(LOG_LEVEL)
formatter = logging.Formatter('%(asctime)s [%(pathname)s:%(lineno)d] %(levelname)8s: %(message)s')
handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(formatter)
log.addHandler(handler)


def main():
    log.info('Starting Telegram Bot...')
    bot.get_update()
    io_loop = ioloop.IOLoop.instance()
    task = ioloop.PeriodicCallback(bot.get_update, PERIODICAL)
    task.start()
    io_loop.start()

if __name__ == '__main__':
    main()
