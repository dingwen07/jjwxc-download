from __future__ import annotations
import requests
import random
from html.parser import HTMLParser
import bs4
from bs4 import BeautifulSoup
import pickle
import os

class JJWXCDownload():
    def __init__(self, novel_id: int) -> None:
        self.set_novel(novel_id)
        self.request_session = requests.Session()

    def set_novel(self, novel_id: int) -> None:
        self.novel_id = novel_id

    def login_getcode(self) -> None:
        url = 'https://m.jjwxc.net//my/login?login_mode=jjwxc'
        self.request_session.get(url)
        auth_code_url = 'https://m.jjwxc.net/codeurl/createCode?var={}'.format(str(random.random()))
        return self.request_session.get(auth_code_url)
    
    def login(self, username: str, password: str, auth_code: str) -> None:
        login_url = 'https://m.jjwxc.net/login/wapLogin'
        referer = 'http://www.jjwxc.net/onebook.php?novelid={}'.format(str(self.novel_id))
        login_data = {
            'referer': referer,
            'login_mode': 'jjwxc',
            'loginname': username,
            'loginpass': password,
            'checkcode': auth_code,
            'cookietime': 1,
            'sub': '%B5%C7+%A1%A1%C8%EB'
        }
        login_response = self.request_session.post(login_url, data=login_data)
        print(login_response.content.decode('GBK'))

    def save_cookies(self):
        with open('cookies.pickle', 'wb') as f:
            pickle.dump(self.request_session.cookies, f)

    def load_cookies(self):
        with open('cookies.pickle', 'rb') as f:
            self.request_session.cookies.update(pickle.load(f))

    def fetch_chapter(self, chapter_no: int, free=True) -> requests.Response:
        if free:
            chapter_url = 'https://m.jjwxc.net/book2/{}/{}'.format(str(self.novel_id), str(chapter_no))
        else:
            chapter_url = 'https://m.jjwxc.net/vip/{}/{}'.format(str(self.novel_id), str(chapter_no))
        return self.request_session.get(chapter_url)

    def get_chapter_text(self, chapter_no: int) -> str:
        text = JJWXCDownload.prase_chapter(self.fetch_chapter(chapter_no))
        if text.find('<返回>') >= 0:
            text = JJWXCDownload.prase_chapter(self.fetch_chapter(chapter_no, False))
        return text

    @staticmethod
    def console_login(jjdown: JJWXCDownload, username='', password='') -> None:
        if username == '':
            username = input('Username> ')
        if password == '':
            password = input('Password> ')
        code_response = jjdown.login_getcode()
        with open('code.jpg', 'wb') as file:
            file.write(code_response.content)
        import tkinter as tk
        root_win = tk.Tk()
        img_code = tk.PhotoImage(file='code.jpg')
        label_img = tk.Label(root_win, image = img_code)
        label_img.pack()
        auth_code = input('VerifyCode> ')
        root_win.destroy()
        jjdown.login(username, password, auth_code)

    @staticmethod
    def prase_chapter(chapter: requests.Response):
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

def JJChapterParser(HTMLParser):
    pass

def get_content_text(tag: bs4.element.Tag):
    text = ''
    for c in tag.contents:
        if isinstance(c, bs4.element.Tag):
            text += get_content_text(c)
        else:
            text += str(c)
    return text

if __name__ == "__main__":
    d = JJWXCDownload(1308990)
    # JJWXCDownload.console_login(d, 'username', 'password')
    d.load_cookies()

    if not os.path.exists('save/{}/'.format(str(d.novel_id))):
        os.makedirs('save/{}/'.format(str(d.novel_id)))

    for c in range(1, 87):
        chapter_text = d.get_chapter_text(c)
        with open('save/{}/{}.txt'.format(str(d.novel_id), str(c)), 'wb') as f:
            f.write(chapter_text.encode('utf-8'))

