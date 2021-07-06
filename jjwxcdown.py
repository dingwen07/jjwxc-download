from __future__ import annotations

import time

import requests
import random
import bs4
import pickle
import os
from bs4 import BeautifulSoup
from selenium import webdriver


class JJWXCDownload:
    def __init__(self, novel_id: int) -> None:
        self.novel_id = novel_id
        self.requests_session = requests.Session()

    def set_novel(self, novel_id: int) -> None:
        self.novel_id = novel_id

    def login_getcode(self) -> requests.Response:
        url = 'https://m.jjwxc.net//my/login?login_mode=jjwxc'
        self.requests_session.get(url)
        auth_code_url = 'https://m.jjwxc.net/codeurl/createCode?var={}'.format(str(random.random()))
        return self.requests_session.get(auth_code_url)

    def login(self) -> None:
        cookies = selenium_login_firefox()
        set_cookies(cookies, self.requests_session)

    def save_cookies(self):
        with open('cookies.pickle', 'wb') as f:
            pickle.dump(self.requests_session.cookies, f)

    def load_cookies(self):
        with open('cookies.pickle', 'rb') as f:
            self.requests_session.cookies.update(pickle.load(f))

    def fetch_chapter(self, chapter_no: int, free=True) -> requests.Response:
        if free:
            chapter_url = 'https://m.jjwxc.net/book2/{}/{}'.format(str(self.novel_id), str(chapter_no))
        else:
            chapter_url = 'https://m.jjwxc.net/vip/{}/{}'.format(str(self.novel_id), str(chapter_no))
        return self.requests_session.get(chapter_url)

    def get_chapter_text(self, chapter_no: int) -> str:
        text = JJWXCDownload.parse_chapter(self.fetch_chapter(chapter_no))
        if text.find('<返回>') >= 0:
            text = JJWXCDownload.parse_chapter(self.fetch_chapter(chapter_no, False))
        return text

    @staticmethod
    def console_login(jjdown: JJWXCDownload, username='', password='') -> None:
        print('WARN: JJWXCDownload.console_login is deprecated ,it has been replaced by JJWXCDownload.login')
        jjdown.login()

    @staticmethod
    def parse_chapter(chapter: requests.Response):
        chapter.encoding = 'GBK'
        # chapter_html = chapter.content.decode('GBK')
        resp = BeautifulSoup(chapter.text, "html.parser")
        uls = resp.findAll("ul")
        text = ''
        for tag in uls[0].contents:
            if isinstance(tag, bs4.element.Tag):
                text += '\n\n[TEXT AREA]\n'
                text += get_content_text(tag)

        # text = get_content_text(uls[0])
        text = text.replace('\u3000\u3000', '\n').strip('\n').strip(' ')
        return text


def get_content_text(tag: bs4.element.Tag):
    text = ''
    for c in tag.contents:
        if isinstance(c, bs4.element.Tag):
            text += get_content_text(c)
        else:
            text += str(c)
    return text


def set_cookies(cookies,
                ua: str = False,
                session: requests.sessions.Session = requests.Session()):
    if ua != False:
        session.headers.update({"user-agent": ua})
    for cookie in cookies:
        session.cookies.set(cookie['name'],
                            cookie['value'],
                            domain=cookie['domain'])
    return session


def selenium_login_firefox():
    print('Please login via the browser then come back.')
    print('DO NOT CLOSE THE BROWSER!!!')
    time.sleep(1)
    browser = webdriver.Firefox()
    browser.get('https://m.jjwxc.net/')
    input('Press <Enter> to continue.')
    cookies = browser.get_cookies()
    browser.close()
    return cookies


if __name__ == "__main__":
    d = JJWXCDownload(1308990)
    d.login()
    d.save_cookies()
    d.load_cookies()

    if not os.path.exists('save/{}/'.format(str(d.novel_id))):
        os.makedirs('save/{}/'.format(str(d.novel_id)))

    for c in range(1, 87):
        chapter_text = d.get_chapter_text(c)
        with open('save/{}/{}.txt'.format(str(d.novel_id), str(c)), 'wb') as f:
            f.write(chapter_text.encode('utf-8'))
