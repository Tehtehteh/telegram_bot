from torndb import Connection
import requests
import logging
from ..config import CHAT_ID

log = logging.getLogger('application')


class TelegramBot:
    telegram_url = "https://api.telegram.org/bot{token}/{method}"
    vk_url = "https://api.vk.com/method/{method}?{params}&access_token={access_token}&v=5.67"
    chat_id = CHAT_ID

    @staticmethod
    def split_message_by_chunks(iterable, step=4096):
        for chunk in range(0, len(iterable), step):
            yield iterable[chunk:chunk + step]

    def __init__(self, token, db_creds, vk_token):
        self.access_token = token
        self.db = Connection(**db_creds)
        self.vk_token = vk_token

    def send_telegram_message(self, text):
        if len(text) > 4096:
            chunk_try = []
            log.info('Sending big message by chunks..')
            for chunk in TelegramBot.split_message_by_chunks(text):
                response = requests.post(self.telegram_url.format(token=self.access_token, method='sendmessage'), json={
                    'text': chunk,
                    'chat_id': self.chat_id
                })
                chunk_try.append(True if response.status_code == 200 else False)
            if all(chunk_try):
                log.info('Good response when sending big message from Telegram..successfully sent message')
            else:
                log.error('Something went wrong when sending big message..')
        else:
            log.info('Sending simple message..')
            response = requests.post(self.telegram_url.format(token=self.access_token, method='sendmessage'), json={
                'text': text,
                'chat_id': self.chat_id
            })
        if response.status_code == 200:
            log.info('Good response from Telegram..successfully sent message')

    def send_request(self, url):
        log.info('Checking VK data ..')
        response = requests.get(url=url)
        res = response.json()
        if response.status_code != 200 or 'error' in res:
            log.error('Something went wrong with response from VK...%s' % (res['error'],))
            return
        res = {x['id']: x['text'] for x in filter(lambda x: '#знакомства_парни' not in x['text'] and
                                                            ('#ищупарня' in x['text'] or
                                                             '#знакомства' in x['text'] or
                                                             '#ищутебя' in x['text']),
                                                  [x for x in res['response']['items']])}
        ids = set(res.keys())
        last = self.db.query("SELECT * FROM messages LIMIT 10")
        new = ids - set(x['id'] for x in last) if last else ids
        if new:
            log.info('Got %s new updates from Odessa Search, querying DB...' % (len(new),))
            self.db.insertmany('INSERT INTO messages set id = %s, message = %s',
                               [(key, str(res[key].encode('utf-8'), 'utf8')) for key in new])
            for i, msg in enumerate(new):
                log.info('Sending messages to Telegram... %s of %s' % (i, len(new)))
                self.send_telegram_message(res[msg])
        else:
            log.warning('No updates from VK...Retrying again in 10 mins...')

    def get_update(self):
        self.send_request(self.vk_url.format(method='wall.get',
                                             params='&'.join(
                                                 [k+'='+v for k, v in
                                                  {'domain': 'odessa.search',
                                                   'count': '10'}.items()]),
                                             access_token=self.vk_token))

