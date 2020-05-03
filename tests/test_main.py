# coding: utf-8
import unittest
import main
import vk


class TestApp(unittest.TestCase):
    def setUp(self):
        session = vk.Session(access_token=main.TOKEN)
        self.api = vk.API(session, v=main.V, lang='ru', timeout=10)

    def test_get_user(self):
        response = self.api.users.get(user_ids=1)
        last_name = response[0]['last_name']
        self.assertEqual(last_name, 'Дуров')

    def test_check_points(self):
        pavel = main.User('1')
        response = self.api.users.get(user_ids=1, fields='city, home_town, sex, bdate, books, '
                                                            'interests, movies, music, personal')
        pavel2 = pavel.get_info(response[0])
        result = main.check_points(pavel, pavel2)
        self.assertTrue(result > 0)

    def test_similarity(self):
        result = main.similarity('съешь ещё этих мягких французских булок', 'съешь ещё этих мягких французских булок')
        self.assertEqual(result, 1.0)

