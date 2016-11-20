import os
from unittest.mock import Mock
from six.moves.urllib import request
from django.conf import settings
from django.contrib.auth.models import User
from django.http.request import HttpRequest
from django.test import Client, TestCase
from .models import Order
from .views import new


def resource(name: str):
    return open(os.path.join(settings.BASE_DIR, 'tests', name), mode='rb')


request.urlopen = Mock(side_effect=[resource('login.xml'),
                                    resource('vinculosPessoaById.json'),
                                    resource('cursoGraduacaoAluno.json')])


class Requests(TestCase):
    def setUp(self):
        self.client = Client()

        self.request = HttpRequest()
        self.request.session = {}

        self.user = User.objects.create_user(username='100000000400000',
                                             password='')

    def test_new_order(self):
        self.client.login(ticket='ST-b91d310a-6d50-45a3-9a1c-1c36fa135ab3',
                          service='http://localhost/?next=%2Forders%2Fnew%2F',
                          request=self.request)

        res = self.client.get('/orders/new/', follow=True)
        self.assertEqual(res.status_code, 200)

        order = Order.objects.get()
        self.assertEqual(order.student, self.user)
        self.assertEqual(len(order.pk), settings.USE_CODE_LENGTH)
