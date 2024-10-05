
import base64
import csv
import random
import shutil
from tempfile import NamedTemporaryFile
from typing import Dict, List
from urllib.request import urlopen
from utils import qb_to_letter, active_qbs

from config import Config

class QBConnectionError(Exception):
    "Raised when there are not enough question banks active"
    pass

class User:
    def __init__(self, csv_row: Dict):
        self.username: str = csv_row['username']
        self.password: str = csv_row['password']

        self.initialised: bool = False
        self.questions: List[str] = None
        self.attempts: List[int] = None
        self.answers: List[str] = None
        self.total_score: int = 0
        self.finished: bool = False

        if (csv_row['questions'] != '-'):
            self.initialised: bool = True
            self.questions: List[str] = csv_row['questions'].split(' ')
            self.attempts: List[int] = [int(attempt) for attempt in csv_row['attempts'].split(' ')]
            self.answers: List[str] = csv_row['current_answer'].split('|')
            self.finished: bool = all(x > 3 for x in self.attempts)

            # 5 = 1st attempt = 3pt
            # 6 = 2nd attempt = 2pt
            # 7 = 3rd attempt = 1pt
            self.total_score: int = sum(3 - (int(attempt) - 5) for attempt in self.attempts if 4 < int(attempt) < 8)

    @classmethod
    def from_cookie(cls, cookie: str):
        username, password = User.decode_login_cookie(cookie)
        return User.from_credentials(username, password)

    @classmethod
    def from_credentials(cls, username: str, password: str):
        tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
        with open('users.csv', mode='r', newline='') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=Config.CSV_FIELDS)
            for row in reader:
                if row['username'] == username and row['password'] == password:
                    return cls(row)
        return None

    def decode_login_cookie(cookie: str):
        try:
            decoded = base64.b64decode(cookie).decode("ascii").split('-')
            return decoded[0], decoded[1]
        except:
            return None, None

    def encode_login_cookie(username, password):
        return base64.b64encode(f"{username}-{password}".encode("ascii")).decode("ascii")

    def initialise(self):
        qb_list = active_qbs()
        print(f"Initialising user {self.username} | {len(qb_list)} active QBs")

        # remove a random QB
        if len(qb_list) == 3:
            random.shuffle(qb_list)
            qb_list.pop()
        elif len(qb_list) < 2:
            raise ConnectionError

        print(f'\tQuerying QBs {qb_list}...')
        questions = []
        for url in qb_list:
            try:
                with urlopen(f"{url}/api/question-list?count=5") as response:
                    out = response.read().decode()
                    questions += [f'{qb_to_letter(url)}{question}' for question in out.split(', ')]
            except Exception as e:
                print(e)
                pass

        random.shuffle(questions)
        question_list = ' '.join(questions)

        print(f'\tQuestions recieved: {question_list}')

        # update the CSV
        tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
        userdata = {}
        with open('users.csv', mode='r', newline='') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=Config.CSV_FIELDS)
            writer = csv.DictWriter(tempfile, fieldnames=Config.CSV_FIELDS)
            for row in reader:
                if row['username'] == self.username and row['password'] == self.password:
                    row['questions'] = question_list
                    row['attempts'] = '1 1 1 1 1 1 1 1 1 1'
                    row['current_answer'] = "||||||||||"
                    userdata = row
                writer.writerow(row)
        shutil.move(tempfile.name, 'users.csv')

        # update current user object to reflect CSV
        self.__init__(userdata)

    def save_answer(self, question_index: int, user_answer: str, correct: bool):
        ''' returns the attempt the user is on after saving the answer'''
        new_attempt = -1

        userdata = {}

        print(f'Saving answer for user {self.username}')
        print(f'\tcorrect: {correct}')
        tempfile = NamedTemporaryFile(mode='w', newline='', delete=False)
        with open('users.csv', mode='r', newline='') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=Config.CSV_FIELDS)
            writer = csv.DictWriter(tempfile, fieldnames=Config.CSV_FIELDS)
            for row in reader:
                if row['username'] == self.username and row['password'] == self.password:
                    # get current users attempts as a list
                    current_attempts = row['attempts'].split(' ')
                    new_attempt = int(current_attempts[question_index])
                    
                    # dont allow a change if the question is already submitted
                    if (new_attempt < 4):
                        new_attempt += 4 if correct else 1

                        current_attempts[question_index] = str(new_attempt)
                        row['attempts'] = ' '.join(current_attempts)

                        # get current users answers as a list
                        current_answers = row['current_answer'].split('|')
                        current_answers[question_index] = str(user_answer)
                        row['current_answer'] = '|'.join(current_answers)
                    userdata = row

                writer.writerow(row)
        shutil.move(tempfile.name, 'users.csv')

        print(f'\tStudent is now on attempt {new_attempt}')

        # update current user object to reflect CSV
        self.__init__(userdata)

        return new_attempt

