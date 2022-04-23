from flask import Flask, request
import logging
from data.user import User
from data.db_session import global_init, create_session
from sqlalchemy import update
import requests
from random import choice, randrange
from photo_manager import ChangedImage, load_image
from results import make_a_score_picture
import os
from hints import letter_unlock, map_hint, image_part_unlock 
import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

dialogs = {}
sessionStorage = {}


class Dialog():
    def __init__(self, user_id, db_user, session):
        self.stage = 1
        self.AUTH_TOKEN = 'OAuth AQAAAABFR7qRAAT7o-z5WS14-E3NgJ6iI4IoUeI'
        self.response = {
                        'session': request.json['session'],
                        'version': request.json['version'],
                        'response': {
                        'end_session': False
                                    }
                        }
        self.score_look = False
        self.get_picture = False
        self.get_message = False
        self.best_score_look = False
        self.user_id = user_id
        self.difficult = None
        self.hints = None
        self.image_count = 0
        self.attempt = 0
        self.game_start = False
        self.game_end = False
        self.session = session
        if db_user is None:
            self.response['response']['text'] = '''Привет! Похоже вы здесь впервые. 
                                                   Я хочу предложить вам сыграть в одну игру, но перед этим, 
                                                   пожалуйста, назовите своё имя, чтобы я знала как к вам обращаться.'''
            self.name = None
            self.user = User(user_id=self.user_id,users_wins=0, users_wins_not_hints=0, score=0, 
                             Alices_wins_not_hints=0, Alices_wins=0)

            self.session.add(self.user)
            self.session.commit()
        else:
            self.response['response']['buttons'] = [
                       {'title': 'да', 'hide': True}, {'title': 'нет', 'hide': True}
                ]
            self.response['response']['text'] = f'''Я рада видеть вас вновь, {db_user.name.capitalize()}! Вы хотите сыграть снова? '''
            self.user = db_user
            self.name = self.user.name.capitalize()
            return
        
    def make_dialog_line(self, req):
        self.update_response()
        self.response['response']['buttons'] = []
        if not self.game_start and self.name is not None:
            if 'счёт' in  req['request']['original_utterance'].lower():
                self.score_look = True
                self.get_picture = False
            
            if req['request']['original_utterance'].lower() == 'таблица лидеров':
                self.best_score_look = True
                self.get_message = False
        if self.score_look:
            self.response['response']['buttons'] += [
                  {'title': 'Выход', 'hide':True}] 
            if not self.get_picture:
                image_name = make_a_score_picture(self.user_id, self.name, 
                                                 self.user.users_wins, self.user.Alices_wins)
                self.score_image_id = self.upload_image(image_name)['image']['id']
                self.response['response']['card'] = {}
                self.response['response']['card']['type'] = 'BigImage'
                if self.user.users_wins > self.user.Alices_wins:
                    title_text = 'Могу вас поздравить с тем, что вы побеждаете!'
                elif self.user.users_wins < self.user.Alices_wins:
                    title_text = 'Я побеждаю! Не так просто отгадать?'
                elif self.user.users_wins == self.user.Alices_wins:
                    title_text = 'Пока что мы идем на равных.'
                elif self.user.users_wins == self.user.Alices_wins == 0:
                    title_text = 'Мы пока еще ни разу не сыграли. Результаты соответствующие.'
                self.response['response']['card']['title'] = title_text
                self.response['response']['card']['image_id'] = self.score_image_id
                self.response['response']['text'] = 'Ой'
                os.remove(image_name)
                self.get_picture = True
                
            elif req['request']['original_utterance'].lower() == 'выход':
                requests.delete(f'https://dialogs.yandex.net/api/v1/skills/f3760eb7-94ec-43f1-8d19-eb5a0ce1caa7/images/{self.score_image_id}', 
                                    headers={'Authorization': self.AUTH_TOKEN}).json()
                self.response['response']['buttons'] = [
                       {'title': 'да', 'hide': True}, {'title': 'нет', 'hide': True}
                ]
                self.stage = 1
                self.hints = None
                self.difficult = None
                self.attempt = 0
                self.score_look = False
                self.response['response']['text'] = 'Напомните, пожалуйста, вы хотите сыграть?'
                

            else: 
                self.response['response']['text'] = 'Скажите "Выход", чтобы вернуться к игре.'
            return
            
        if self.best_score_look:
            self.response['response']['buttons'] += [
                  {'title': 'Выход', 'hide':True}] 
            if not self.get_message:
                i = 1
                query = self.session.query(User).order_by(User.score.desc()).limit(10)
                self.response['response']['text'] = 'Эти люди лучше всех отгадывают картинки:\n'
                for user in query:
                    self.response['response']['text'] += str(i) + '. ' + user.name + ' ' + str(user.score) + ' очков\n'
                    i += 1
                self.get_message = True
                
            elif req['request']['original_utterance'].lower() == 'выход':
                self.response['response']['buttons'] = [
                       {'title': 'да', 'hide': True}, {'title': 'нет', 'hide': True}
                ]
                self.best_score_look = False
                self.stage = 1
                self.hints = None
                self.difficult = None
                self.attempt = 0
                self.score_look = False
                self.response['response']['text'] = 'Напомните, пожалуйста, вы хотите сыграть?'
                

            else: 
                self.response['response']['text'] = 'Скажите "Выход", чтобы вернуться к игре.'
            return

        if self.name is None:
            possible_name = req['request']['original_utterance']
            self.response['response']['buttons'] = [
                       {'title': 'да', 'hide': True}, {'title': 'нет', 'hide': True}
                ]
            self.response['response']['text'] = f'Приятно познакомиться, {possible_name}. ' \
                                                f'Я обьясню правила игры:' \
                                                f'Я нахожу картинку в интернете, придаю ей немного '\
                                                f'другой вид, а вы пытаетесь отгадать' \
                                                f'что изображено на картинке.У вас есть три попытки. Хотите сыграть?'
            self.user.name = possible_name

            self.name = possible_name.capitalize()
            return
        elif self.stage == 1:
            self.ask_for_difficult(req, 'Перед началом игры давайте определим уровень сложности от 1 до 3.')
            self.response['response']['buttons'] = [
                       {'title': '1', 'hide': True}, {'title': '2', 'hide': True}, 
                       {'title': '3', 'hide': True}
                ]
            return
            
        if self.difficult is None:
            difficult = self.get_difficult(req)
            if difficult is None:
                self.response['response']['text'] = 'Я не очень вас поняла.'
            else:
                self.difficult = difficult
                asked_image = ChangedImage(self.original_image_name)
                asked_image.change_picture('reverse', self.difficult)
                self.new_uploaded_image_id = self.upload_image(self.new_image_name)['image']['id']
                self.response['response']['text'] = 'Вы хотите играть с подсказками?\n' \
                                                    'Игры, в которых были использованы подсказки ' \
                                                    'не будут отображаться в общей статистике'
                self.response['response']['buttons'] = [
                       {'title': 'да', 'hide': True}, {'title': 'нет', 'hide': True}
                ]
            return
        if self.hints is None:
            self.game_start = True
            agree_for_hints = self.get_agreement(req)
            if agree_for_hints is None:
                self.game_start = False
                self.response['response']['text'] = 'Я не очень вас поняла.'
                return
            elif agree_for_hints:
                self.hints = True
                self.uploaded_hint = ''
            else:
                self.hints = False
        
        if self.game_start:
            self.uploaded_hint = ''
            if self.hints:
                self.response['response']['buttons'] = [{'title': 'Подсказка', 'hide': True}]
            
                if 'подсказк' in req['request']['original_utterance'].lower():
                    type_of_hint = randrange(3)
                    if type_of_hint == 0:
                        hint = map_hint(self.category, self.name, self.user_id)
                        self.uploaded_hint = self.upload_image(hint)['image']['id']
                        self.response['response']['card'] = {}
                        self.response['response']['card']['type'] = 'BigImage'
                        self.response['response']['card']['title'] = 'Здесь должно быть что-то, что может вам помочь.'
                        self.response['response']['card']['image_id'] = self.uploaded_hint   
                        self.response['response']['text'] = 'Ой'
                        os.remove(hint)
                
                    elif type_of_hint == 1:
                        hint = image_part_unlock(self.original_image_name, self.user_id, self.name)
                        self.uploaded_hint = self.upload_image(hint)['image']['id']
                        self.response['response']['card'] = {}
                        self.response['response']['card']['type'] = 'BigImage'
                        self.response['response']['card']['title'] = 'Вот часть оригинала для вас.'
                        self.response['response']['card']['image_id'] = self.uploaded_hint   
                        self.response['response']['text'] = 'Ой'
                        os.remove(hint) 
                       
                    elif type_of_hint == 2:
                        hint = letter_unlock(self.text[0])
                        self.response['response']['text'] = f'Буква "{hint[0]}", откройте!\n {hint[1]}'
                    return
                
            if self.attempt == 0:
                self.response['response']['card'] = {}
                self.response['response']['card']['type'] = 'BigImage'
                self.response['response']['card']['title'] = 'Угадайте что здесь.'
                self.response['response']['card']['image_id'] = self.new_uploaded_image_id   
                self.response['response']['text'] = 'Ой'
            elif self.attempt == 1:
                self.response['response']['text'] = 'Вы не угадали, попробуете еще.' + (
                                                       'Если вы хотите подсказку, скажите "подсказка"' if self.hints else '')
            elif self.attempt == 2:
                self.response['response']['text'] = 'К сожалению, вы снова не угадали. У вас осталась 1 попытка'
                
            elif self.attempt == 3:
                self.response['response']['buttons'] = [
                  {'title': 'Таблица Лидеров', 'hide':False}, 
                  {'title': 'Счёт', 'hide': False},
                  {'title': 'да', 'hide': True}, 
                  {'title': 'нет', 'hide': True}
            ] 
                self.game_end = True
                self.original_uploaded_image_id = self.upload_image(self.original_image_name + '.png')['image']['id']
                self.response['response']['card'] = {}
                self.response['response']['card']['type'] = 'BigImage'
                self.response['response']['card']['title'] = f'В этот раз победила я. Правильный ответ: {self.text[0]}. Хотите еще раз сыграть?'
                self.response['response']['card']['image_id'] = self.original_uploaded_image_id   
                self.response['response']['text'] = 'Ой'
                self.game_start = False
            if self.compare_answers(req):
                self.game_end = True
                self.response['response']['buttons'] = [
                  {'title': 'Таблица Лидеров', 'hide':False}, 
                  {'title': 'Счёт', 'hide': False},
                  {'title': 'да', 'hide': True}, 
                  {'title': 'нет', 'hide': True}
            ] 
                self.original_uploaded_image_id = self.upload_image(self.original_image_name + '.png')['image']['id']
                self.response['response']['card'] = {}
                self.response['response']['card']['type'] = 'BigImage'
                self.response['response']['card']['title'] = f'Вы правы - это {self.text[0]}. Хотите сыграть еще?'
                self.user.users_wins += 1
                self.user.score += 1000 * self.difficult
                self.session.commit()
                if not self.hints:
                    self.user.users_wins_not_hints += 1
                self.response['response']['card']['image_id'] = self.original_uploaded_image_id   
                self.response['response']['text'] = 'Ой'
                self.game_start = False
            elif self.attempt == 3:
                self.user.Alices_wins += 1
                if not self.hints:
                    self.user.Alices_wins_not_hints += 1
                self.user.score -=  1000
                self.session.commit()
            else:
                self.attempt += 1   
            return

        if self.game_end:
            os.remove(self.original_image_name + '.png')
            os.remove(self.new_image_name)
            requests.delete(f'https://dialogs.yandex.net/api/v1/skills/f3760eb7-94ec-43f1-8d19-eb5a0ce1caa7/images/{self.uploaded_hint}', 
                                  headers={'Authorization': self.AUTH_TOKEN}).json()
            print(requests.delete(f'https://dialogs.yandex.net/api/v1/skills/f3760eb7-94ec-43f1-8d19-eb5a0ce1caa7/images/{self.original_uploaded_image_id}', 
                                  headers={'Authorization': self.AUTH_TOKEN}).json())
            print(requests.delete(f'https://dialogs.yandex.net/api/v1/skills/f3760eb7-94ec-43f1-8d19-eb5a0ce1caa7/images/{self.new_uploaded_image_id}', 
                                    headers={'Authorization': self.AUTH_TOKEN}).json())                        
            agree = self.get_agreement(req)
            if agree:
                self.stage = 1
                self.hints = None
                self.difficult = None
                self.attempt = 0
                self.ask_for_difficult(req, 'Давайте снова определимся со всеми параметрами. \n Выберите сложность от 1 до 3')
            elif agree is False:
                self.response['response']['text'] = f'Спасибо за игру, {self.name}. Еще увидимся!'
                self.response['response']['end_session'] = True
            elif agree is None:
                self.response['response']['text'] = 'Я не очень вас поняла.'
            

    def upload_image(self, image_name):
        with open(image_name, 'rb') as img:
            return requests.post('https://dialogs.yandex.net/api/v1/skills/f3760eb7-94ec-43f1-8d19-eb5a0ce1caa7/images', 
                     files={'file': (image_name, img)}, 
                     headers={'Authorization': self.AUTH_TOKEN}).json()

    def get_image_text(self):
        with open('words', 'r', encoding='utf-8') as file:
            line = choice(file.read().split('\n'))
            self.category = line.split(':')[0]
            text = choice((line.split(':')[1]).split())
            return (text, self.category)

    def get_response(self):
        return self.response
    
    def ask_for_difficult(self, req, text):
        agree = self.get_agreement(req)
        if agree:
            self.response['response']['text'] = text
            self.original_image_name = self.user_id + '-+-+-' + str(self.image_count)
            self.new_image_name = self.original_image_name + '-new.png' 
            self.text = self.get_image_text()
            load_image(self.text[0] + '-' + self.text[1], self.original_image_name)
            self.stage += 1
        elif agree is False:
            self.response['response']['text'] = 'Очень жаль.'
            self.response['response']['end_session'] = True
        elif agree is None:
            self.response['response']['text'] = 'Я не очень вас поняла.'


    def get_difficult(self, req):
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.NUMBER':
                if entity['value'] in [1, 2, 3]:
                    return entity['value']

    def get_agreement(self, req):
        if 'да' in req['request']['original_utterance'].lower():
            return True
        elif 'не' in req['request']['original_utterance'].lower():
            return False

    def update_response(self):
        self.response = self.response = {
                        'session': request.json['session'],
                        'version': request.json['version'],
                        'response': {
                        'end_session': False
                                    }
                        }
    

    def compare_answers(self, req):
        if self.text[0] in req['request']['original_utterance'].lower():
            return True 


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
     
    req = request.json
    user_id = req['session']['user_id']
    if req['session']['new']:
        db_sess = create_session()
        db_user = db_sess.query(User).filter(User.user_id == user_id).first()
        dialogs[user_id] = Dialog(user_id, db_user, db_sess)
        response = dialogs[user_id].get_response()
        return json.dumps(response)
    
    else:
        current_dialog = dialogs[user_id]
        current_dialog.make_dialog_line(req)
        response = dialogs[user_id].get_response()
        return json.dumps(response)


if __name__ == '__main__':
    global_init("db/database.db")
    app.run()