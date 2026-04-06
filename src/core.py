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
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.load_tid()

    def load_tid(self):
        tid = self.cursor.execute('select val from kv where key = "current_tid"').fetchone()[0]
        self.t_id = int(tid)

    def save_tid(self):
        self.cursor.execute(f'update kv set val = "{self.t_id}" where key = "current_tid"')
        self.conn.commit()

    def generate_question(self, uid):
        active, start_t, cq = self.cursor.execute(f'select active, start_t, current_q from users where id = {uid}').fetchone()

        if int(active) != 1:
            return None

        q_path = media_path / f"tests/{self.t_id}/{cq}.{EXTENSION}"
        remaining_t = start_t + (70 * 60)

        return cq, q_path, remaining_t, self.generate_brutal_string(uid)

    def generate_brutal_string(self, uid):
        solved_q = {row[0] for row in self.cursor.execute(
            f'select q_id from answers where id = {uid} and t_id = {self.t_id}'
        ).fetchall()}

        cells = ["[✓]" if i in solved_q else f"[{i}]" for i in range(1, 45)]
        rows = [cells[i:i + 10] for i in range(0, 44, 10)]
        return "\n".join(" ".join(row) for row in rows)

    def has_active_users(self):
        row = self.cursor.execute('select count(*) from users where active = 1').fetchone()
        return row[0] > 0

    def get_expired_users(self):
        deadline = time.time() - (70 * 60)
        rows = self.cursor.execute(f'select id from users where active = 1 and start_t < {deadline}').fetchall()
        return [row[0] for row in rows]

    def is_active(self, uid):
        row = self.cursor.execute(f'select active from users where id = {uid}').fetchone()
        return row is not None and row[0] == 1

    def answer_q(self, uid, ans):
        cq = self.cursor.execute(f'select current_q from users where id = {uid}').fetchone()[0]

        self.cursor.execute(f'insert into answers (id, t_id, q_id, answer) values ({uid}, {self.t_id}, {cq}, "{ans}")')

        next_q = cq + 1 if cq != QUESTION_NUM else 1
        self.cursor.execute(f'update users set current_q = {next_q} where id = {uid}')
        self.conn.commit()

    def switch_q(self, uid, qid):
        if qid < 1 or qid > 44:
            return 1

        self.cursor.execute(f'update users set current_q = {qid} where id = {uid}')
        self.conn.commit()
        return 0

    def info(self, uid):
        active = self.cursor.execute(f'select active from users where id={uid}').fetchone()

        return active

    def start_test(self, uid):
        row = self.cursor.execute(f'select active from users where id={uid}').fetchone()

        if row is None:
            return None

        active = row[0]

        if active == 0:
            self.cursor.execute(f'update users set active = 1 where id = {uid}')
            self.cursor.execute(f'update users set start_t = {time.time()} where id = {uid}')
            self.cursor.execute(f'update users set current_q = 1 where id = {uid}')
            self.conn.commit()

            return 0

        return active

    def finish_test(self, uid):
        self.cursor.execute(f'update users set active = 2 where id = {uid}')
        self.conn.commit()

    def new_test(self):
        self.t_id += 1

        self.save_tid()

        self.cursor.execute('update users set active = 0')
        self.cursor.execute('update users set current_q = 1')
        self.conn.commit()


