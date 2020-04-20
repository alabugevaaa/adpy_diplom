import json
import os
import time
import vk
import difflib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlencode
from orm import add_result, get_top, delete_all, get_or_create, set_shown


TOKEN = os.getenv('VK_TOKEN')
APP_ID = os.getenv('APP_ID')
V = '5.103'
# BASE_URL = 'https://oauth.vk.com/authorize'
# auth_data = {
#     'client_id': APP_ID,
#     'display': 'page',
#     'response_type': 'token',
#     'scope': 'friends',
#     'v': '5.95'
# }
#
# print('?'.join((BASE_URL, urlencode(auth_data))))


class User:

    def __init__(self, user='0'):
        session = vk.Session(access_token=TOKEN)
        self.api = vk.API(session, v=V, lang='ru', timeout=20)
        response = self.api.users.get(user_ids=user, fields='city, home_town, sex, bdate, books, '
                                                            'interests, movies, music, personal')
        if 'error_code' not in response:
            response = response[0]

            if response.get('deactivated') == 'banned':
                raise Exception('Страница пользователя заблокировна')
            elif response.get('deactivated') == 'deleted':
                raise Exception('Страница пользователя удалена')

            if response['is_closed'] and not response['can_access_closed']:
                raise Exception('Профиль скрыт настройками приватности')

            self.user_id, self.first_name, self.last_name, self.sex, self.age, city, self.hometown, \
            self.personal, self.interests, self.books, self.movies, self.music, self.groups = self.get_info(response)

            if city:
                self.city = city['title']
                self.city_id = city['id']
            else:
                self.city = input('Укажите ваш город: ')
                try:
                    id = self.api.database.getCities(country_id=1, q=self.city)['items']
                    self.city_id = id[0]
                except:
                    self.city_id = ''
            if not self.age:
                self.age = int(input('Укажите Ваш возраст: '))
            if not self.sex:
                sex = input('Укажите Ваш пол (м/ж): ')
                self.sex = 1 if sex == 'ж' else 2

        else:
            raise Exception(response['error_msg'])

    def __repr__(self):
        return f'https://vk.com/id{self.user_id}'

    def get_info(self, response):
        user_id = response['id']
        first_name = response['first_name']
        last_name = response['last_name']

        sex = response.get('sex')
        if response.get('bdate') and len(response.get('bdate')) > 7:
            bdate = datetime.strptime(response.get('bdate'), '%d.%m.%Y').date()
            age = relativedelta(datetime.today(), bdate).years
        else:
            age = ''
        city = response.get('city')
        hometown = response.get('home_town', '')
        personal = response.get('personal', {})
        interests = response.get('interests', '')
        books = response.get('books', '')
        movies = response.get('movies', '')
        music = response.get('music', '')
        while True:
            try:
                groups = set(self.api.groups.get(user_id=response['id'])['items'])
            except vk.exceptions.VkAPIError as vk_error:
                if vk_error.code == 6:
                    time.sleep(1)
                else:
                    groups = set()
                    break
                continue
            break

        return user_id, first_name, last_name, sex, age, city, hometown, \
            personal, interests, books, movies, music, groups

    def check_points(self, params):
        user_id, first_name, last_name, sex, age, city, hometown, \
            personal, interests, books, movies, music, groups = params
        points = 0

        while True:
            try:
                common_count = len(self.api.friends.getMutual(source_uid=self.user_id, target_uid=user_id))
            except vk.exceptions.VkAPIError as vk_error:
                if vk_error.code == 6:
                    time.sleep(1)
                continue
            break

        if common_count > 0:
            points += 20
        common_groups = len(groups & self.groups)
        if common_groups > 0:
            points += 16
        if city:
            city = city['title']
        if city == self.city:
            points += 13
        if isinstance(age, int) and self.age - 5 <= age <= self.age + 5:
            points += 10
        if hometown != '' and hometown.lower() == self.hometown.lower():
            points += 5
        if personal != '' and self.personal != '':
            if personal.get('political') is not None and personal.get('political') != 0 \
                    and personal.get('political') == self.personal.get('political'):
                points += 2
            if personal.get('religion') is not None and personal.get('religion') != 0 \
                    and personal.get('religion') == self.personal.get('religion'):
                points += 2
            if personal.get('people_main') is not None and personal.get('people_main') != 0 \
                    and personal.get('people_main') == self.personal.get('people_main'):
                points += 2
            if personal.get('life_main') is not None and personal.get('life_main') != 0 \
                    and personal.get('life_main') == self.personal.get('life_main'):
                points += 2
            if personal.get('smoking') is not None and personal.get('smoking') != 0 \
                    and personal.get('smoking') == self.personal.get('smoking'):
                points += 2
            if personal.get('alcohol') is not None and personal.get('alcohol') != 0 \
                    and personal.get('alcohol') == self.personal.get('alcohol'):
                points += 2
        if interests != '':
            degree = similarity(interests, self.interests)
            points += 7 * degree
        if music != '':
            degree = similarity(music, self.music)
            points += 6 * degree
        if movies != '':
            degree = similarity(movies, self.movies)
            points += 5 * degree
        if books != '':
            degree = similarity(books, self.books)
            points += 4 * degree

        return points

    def search(self):
        sex_oppos = 1 if self.sex == 2 else 2
        while True:
            try:
                result = self.api.users.search(count=1000, sex=sex_oppos, age_from=self.age-5, age_to=self.age+5,
                                               city=self.city_id, has_photo=1,
                                               fields='city, home_town, sex, bdate, books, interests, movies, '
                                                      'music, personal, relation')['items']
            except vk.exceptions.VkAPIError as vk_error:
                if vk_error.code == 6:
                    time.sleep(1)
                continue
            break

        for r in result:
            if (r['is_closed'] and not r['can_access_closed']) \
                    or r.get('relation') in (2, 3, 4, 5, 7, 8):
                continue

            points = self.check_points(self.get_info(r))

            # если статус "в активном поиске" добавляем баллы
            if r.get('relation') == 6:
                points += 2

            if points > 20:
                while True:
                    try:
                        photos = self.api.photos.get(owner_id=r['id'], album_id='profile', extended=1)['items']
                    except vk.exceptions.VkAPIError as vk_error:
                        if vk_error.code == 6:
                            time.sleep(1)
                        continue
                    break
                top = {}
                for photo in photos:
                    url_photo = photo['sizes'][1]['url']
                    count_likes = photo['likes']['count']
                    top[url_photo] = count_likes
                sorted_top = sorted(top.items(), key=lambda x: x[1])[:3]
                if len(sorted_top) == 3:
                    get_or_create(user_id=self.user_id, link=f'https://vk.com/id{r["id"]}', points=points,
                                  top1=sorted_top[0][0], top2=sorted_top[1][0], top3=sorted_top[2][0])

    def get_result_search(self, count):
        result = []
        for row in get_top(self.user_id, count):
            data = {
                'link': row.link,
                'points': row.points,
                'top1': row.top1,
                'top2': row.top2,
                'top3': row.top3
            }
            result.append(data)
            set_shown(row.id)

        with open("result_search.json", "w") as write_file:
            json.dump(result, write_file, ensure_ascii=False, indent=2)


def similarity(s1, s2):
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


if __name__ == '__main__':
    user = User('eshmargunov')
    user.search()
    user.get_result_search(10)
