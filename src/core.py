import os
import sqlite3
import dotenv
import time
import pathlib

EXTENSION="jpg"
QUESTION_NUM=44

dotenv.load_dotenv()
media_path = os.getenv("MEDIA_PATH")

if media_path is None:
    quit("Unspecified media folder path!")

media_path = pathlib.Path(media_path)
db_path = media_path / "data.db"


class Core:
    def __init__(self):
        self.t_id = 0
        self.cursor = sqlite3.connect(db_path.name).cursor()

        self.load_tid()

    def load_tid(self):
        tid = self.cursor.execute('select val from kv where key = "current_tid"').fetchone()
        self.t_id = int(tid)

    def save_tid(self):
        self.cursor.execute(f'update kv set val = "{self.t_id}" where key = "current_tid"')

    def generate_question(self, uid):
        active, start_t, cq = self.cursor.execute(f'select active, start_t, current_q from users where id = {uid}').fetchone()

        if int(active) != 1:
            return None

        q_path = media_path / f"tests/{self.t_id}/{cq}.{EXTENSION}"
        remaining_t = start_t + (70 * 60)

        return cq, q_path, remaining_t

    def answer_q(self, uid, qid, ans):
        self.cursor.execute(f'insert into answers (id, t_id, q_id, answer) values ({uid}, {self.t_id}, {qid}, "{ans}")')

        if qid != QUESTION_NUM:
            qid += 1
        else:
            qid = 1

        self.cursor.execute(f'update users set current_q = {qid} where id = {uid}')

    def switch_q(self, uid, qid):
        if qid < 1 or qid > 44:
            return 1

        self.cursor.execute(f'update users set q_id = {qid} where id = {uid}')
        return 0

    def info(self, uid):
        active = self.cursor.execute(f'select active from users where id={uid}').fetchone()

        return active

    def start_test(self, uid):
        active = self.cursor.execute(f'select active from users where id={uid}').fetchone()

        if active == 0:
            self.cursor.execute(f'update users set active = 1 where id = {uid}')
            self.cursor.execute(f'update users set start_t = {time.time()} where id = {uid}')
            self.cursor.execute(f'update users set current_q = 1 where id = {uid}')

            return 0

        else:
            return active

    def finish_test(self, uid):
        self.cursor.execute(f'update users set active = 2 where id = {uid}')

    def new_test(self):
        self.t_id += 1

        self.save_tid()

        self.cursor.execute('update users set active = 0')
        self.cursor.execute('update users set current_q = 1')


