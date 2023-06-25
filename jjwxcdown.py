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
    def __init__(self, novel_id: int, browser = None) -> None:
        self.novel_id = novel_id
        self.requests_session = requests.Session()
        self.browser = browser
        self.cookies: list = []
        # set user agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        self.requests_session.headers.update({"user-agent": user_agent})

    def set_novel(self, novel_id: int) -> None:
        self.novel_id = novel_id

    def login_getcode(self) -> requests.Response:
        url = 'https://m.jjwxc.net//my/login?login_mode=jjwxc'
        self.requests_session.get(url)
        auth_code_url = 'https://m.jjwxc.net/codeurl/createCode?var={}'.format(str(random.random()))
        return self.requests_session.get(auth_code_url)

    def login(self) -> None:
        # cookies = selenium_login_firefox()
        self.selenium_login(close_browser=False)
        set_cookies(self.cookies, self.requests_session)

    def save_cookies(self):
        with open('cookies.pickle', 'wb') as f:
            pickle.dump(self.cookies, f)

    def load_cookies(self):
        with open('cookies.pickle', 'rb') as f:
            self.cookies = pickle.load(f)
            set_cookies(self.cookies, self.requests_session)
            if self.browser:
                self.browser.get('https://m.jjwxc.net/')
                for cookie in self.cookies:
                    self.browser.add_cookie(cookie)

    def fetch_chapter(self, chapter_no: int, free=True) -> requests.Response:
        if free:
            chapter_url = 'https://m.jjwxc.net/book2/{}/{}'.format(str(self.novel_id), str(chapter_no))
            response = self.requests_session.get(chapter_url)
            response.encoding = 'GBK'
            return response.text
        else:
            chapter_url = 'https://m.jjwxc.net/vip/{}/{}'.format(str(self.novel_id), str(chapter_no))
            if not self.browser:
                print('ERROR: No browser found.')
                return
            # get using selenium
            # wait javascript to load
            self.browser.get(chapter_url)
            time.sleep(5)
            # get html
            chapter_html = self.browser.page_source
            return chapter_html

    def get_chapter_text(self, chapter_no: int) -> str:
        text = JJWXCDownload.parse_chapter(self.fetch_chapter(chapter_no))
        if text.find('<返回>') >= 0:
            text = JJWXCDownload.parse_chapter(self.fetch_chapter(chapter_no, False))
        return text

    def selenium_login(self, close_browser=True) -> None:
        if (not self.browser):
            print('ERROR: No browser found.')
            return
        print('Please login via the browser then come back.')
        print('DO NOT CLOSE THE BROWSER!!!')
        time.sleep(1)
        self.browser.get('https://m.jjwxc.net/')
        input('Press <Enter> to continue.')
        self.cookies = self.browser.get_cookies()
        if close_browser:
            self.browser.close()

    @staticmethod
    def console_login(jjdown: JJWXCDownload, username='', password='') -> None:
        print('WARN: JJWXCDownload.console_login is deprecated ,it has been replaced by JJWXCDownload.login')
        jjdown.login()

    @staticmethod
    def parse_chapter(chapter: str) -> str:
        # chapter.encoding = 'GBK'
        # chapter_html = chapter.content.decode('GBK')
        resp = BeautifulSoup(chapter, "html.parser")
        uls = resp.findAll("ul" , {"class": "content_ul"})
        text = ''
        if len(uls) == 0:
            print('WARN: No ul tag found.')
            # print(chapter)
            text += '<返回>'
        else:
            for tag in uls[0].contents:
                if isinstance(tag, bs4.element.Tag) and tag.name == 'li':
                    text += os.linesep
                    text += '[TEXT AREA]'
                    text += os.linesep
                    text += JJWXCDownload.get_content_text(tag)

        # text = get_content_text(uls[0])
        text = text.replace('\u3000\u3000', '\n').strip('\n').strip(' ')
        return text

    @staticmethod
    def get_content_text(tag: bs4.element.Tag):
        text = ''
        for c in tag.contents:
            if isinstance(c, bs4.element.Tag):
                if not c.name == 'script':
                    text += JJWXCDownload.get_content_text(c)
            else:
                content = str(c).strip('\n').strip(' ')
                if len(content) > 3:
                    content += os.linesep
                text += content
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


def get_selenium_browser_firefox() -> webdriver.Firefox:
    browser = webdriver.Firefox()
    return browser

def get_selenium_browser_chrome() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.binary_location = 'C:\Program Files\Google\Chrome Dev\Application\chrome.exe'
    browser = webdriver.Chrome(options=options)
    return browser

if __name__ == "__main__":
    d = JJWXCDownload(4472959, browser=get_selenium_browser_chrome())
    # d.login()
    # d.save_cookies()
    d.load_cookies()

    if not os.path.exists('save/{}/'.format(str(d.novel_id))):
        os.makedirs('save/{}/'.format(str(d.novel_id)))

    for c in range(1, 2):
        chapter_text = d.get_chapter_text(c)
        with open('save/{}/{}.txt'.format(str(d.novel_id), str(c)), 'wb') as f:
            f.write(chapter_text.encode('utf-8'))
