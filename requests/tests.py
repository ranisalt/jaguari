import os
from unittest.mock import Mock
from six.moves.urllib import request
from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from .models import Order
from .views import new


def resource(name: str):
    return open(os.path.join(settings.BASE_DIR, 'tests', name), mode='rb')


request.urlopen = Mock(side_effect=[resource('vinculosPessoaById.json'),
                                    resource('cursoGraduacaoAluno.json')])


class Requests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='100000000400000')

    def test_new_order(self):
        req = self.factory.get('/orders/new/')
        req.session = {}
        req.user = self.user

        res = new(req)
        self.assertEqual(res.status_code, 200)

        order = Order.objects.get(id=req.session['order'])
        self.assertEqual(order.student, self.user)
        self.assertEqual(len(order.pk), settings.USE_CODE_LENGTH)
