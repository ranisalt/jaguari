import iso8601
import os
import random
import responses
from django.conf import settings
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from .factories import DegreeJSONFactory, OrderFactory, StudentJSONFactory, \
    UserFactory
from .models import Degree


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'fixtures', name), mode)


def ws(*args):
    return 'https://ws.ufsc.br/{}'.format('/'.join(args))


@override_settings(MEDIA_ROOT='/tmp/upload', PAGSEGURO_SANDBOX=True)
class Orders(TransactionTestCase):
    def setUp(self):
        self.responses = responses.RequestsMock()
        self.responses.__enter__()

        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_list_orders(self):
        OrderFactory.create_batch(5)
        OrderFactory.create_batch(5, student=self.user)

        response = self.client.get(reverse('orders:index'))
        self.assertTemplateUsed(response, 'orders/order_list.html')

        orders = response.context['object_list']

        # users should see all anf only their orders
        self.assertEqual(5, orders.count())
        for order in orders:
            self.assertEqual(self.user, order.student)

    def test_detail_order(self):
        order = OrderFactory(student=self.user)

        response = self.client.get(reverse('orders:detail', kwargs={
            'pk': str(order.pk),
        }))
        self.assertTemplateUsed(response, 'orders/order_detail.html')

        object = response.context['object']
        self.assertEqual(self.user, order.student)
        self.assertEqual(object.birthday, order.birthday)
        self.assertEqual(object.cpf, order.cpf)
        self.assertEqual(object.identity_number, order.identity_number)
        self.assertEqual(object.identity_issuer, order.identity_issuer)
        self.assertEqual(object.identity_state, order.identity_state)
        self.assertEqual(object.enrollment_number, order.enrollment_number)

    def test_new_order(self):
        student_json = StudentJSONFactory.build(ativo=True)

        degree_json = DegreeJSONFactory.build()
        self.responses.add(
            method=responses.GET,
            url=ws('CAGRService', 'cursoGraduacaoAluno', student_json['id']),
            json=degree_json)

        links_json = StudentJSONFactory.build_batch(random.randrange(3))
        links_json.append(student_json)
        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=links_json)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'orders/new.html')

        object = response.context['object']
        self.assertEqual(self.client.session['order'], str(object.pk))
        self.assertEqual(self.user, object.student)
        self.assertEqual(
            iso8601.parse_date(student_json['dataNascimento']).date(),
            object.birthday)
        self.assertEqual(str(student_json['cpf']), object.cpf)
        self.assertEqual(student_json['identidade'], object.identity_number)
        self.assertEqual(student_json['siglaOrgaoEmissorIdentidade'],
                         object.identity_issuer)
        self.assertEqual(student_json['codigoUfIdentidade'],
                         object.identity_state)
        self.assertEqual(student_json['matricula'], object.enrollment_number)

        degree = object.degree
        self.assertEqual(Degree.UNDERGRADUATE, degree.tier)
        self.assertEqual(degree_json['nomeCompleto'], degree.name)
        self.assertEqual(degree_json['campus']['id'], degree.campus)

    def test_post_new_order(self):
        order = OrderFactory(student=self.user)

        session = self.client.session
        session['order'] = str(order.pk)
        session.save()

        with resource('checkout.xml') as payload:
            self.responses.add(
                method=responses.POST,
                url='https://ws.sandbox.pagseguro.uol.com.br/v2/checkout',
                body=payload.read(),
                content_type='application/xml')

            with resource('image.jpg', 'rb') as picture:
                response = self.client.post(reverse('orders:create'), {
                    'picture': picture
                })

        # ensure response is redirect to payment gateway
        self.assertRedirects(response,
                             'https://sandbox.pagseguro.uol.com.br/v2/checkout/payment.html?code=00000000000000000000000000000000',
                             fetch_redirect_response=False)

    def tearDown(self):
        self.responses.__exit__()
