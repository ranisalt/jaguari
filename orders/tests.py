import copy
import os
import responses
import datetime
from django.conf import settings
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from .factories import DegreeFactory, OrderFactory, TransactionFactory, \
    UserFactory


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'fixtures', name), mode)


def ws(*args):
    return 'https://ws.ufsc.br/{}'.format('/'.join(args))


@override_settings(MEDIA_ROOT='/tmp/upload', PAGSEGURO_SANDBOX=True)
class Orders(TransactionTestCase):
    links = [{
        'ativo': True,
        'id': '15100000',
        'idPessoa': '100000000400000',
        'codigoVinculo': 1,
        'codigoCurso': 123,
        'dataNascimento': '1996-01-01T00:00:00-03:00',
        'cpf': 12345678901,
        'identidade': '1234567',
        'codigoUfIdentidade': 'SC',
        'siglaOrgaoEmissorIdentidade': 'SSP',
        'codigoSituacao': 0,
    }]

    def assertDictContainsSubset(self, subset, dictionary, msg=None):
        for attr in subset:
            self.assertEqual(subset[attr], dictionary[attr], msg)

    def setUp(self):
        self.responses = responses.RequestsMock()
        self.responses.__enter__()

        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_list_orders(self):
        OrderFactory.create_batch(5)
        OrderFactory.create_batch(3, student=self.user)

        response = self.client.get(reverse('orders:index'))
        self.assertTemplateUsed(response, 'orders/order_list.html')

        orders = response.context['object_list']

        # users should see all anf only their orders
        self.assertEqual(3, orders.count())
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
        self.responses.add(
            method=responses.GET,
            url=ws('CAGRService', 'cursoGraduacaoAluno', '15100000'),
            json={
                'codigo': 123,
                'nomeCompleto': 'Science Engineering',
                'campus': {'id': 1},
            })

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=self.links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'orders/order_form.html')

        initial = response.context['form'].initial
        self.assertDictContainsSubset({
            'student_id': self.user.pk,
            'degree_id': 123,
            'birthday': datetime.date(1996, 1, 1),
            'cpf': '12345678901',
            'identity_number': '1234567',
            'identity_issuer': 'SSP',
            'identity_state': 'SC',
            'enrollment_number': '15100000',
        }, initial)

    def test_new_order_missing_field(self):
        broken_links = copy.deepcopy(self.links)
        del broken_links[0]['siglaOrgaoEmissorIdentidade']

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/missing_fields.html')

    def test_new_order_no_active_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['ativo'] = False

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    def test_new_order_no_regular_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['codigoSituacao'] += 1

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    def test_new_order_no_undergraduate_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['codigoVinculo'] += 1

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    def test_post_new_order(self):
        degree = DegreeFactory(id=123)

        self.responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=self.links)

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

    def test_order_transaction_status_filter(self):
        from pagseguro.admin import TransactionAdmin
        from pagseguro.models import Transaction
        from .admin import TransactionStatusFilter
        from .models import Order

        for order in OrderFactory.create_batch(5):
            TransactionFactory(reference=str(order.pk))

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk), status='pago')

        filter = TransactionStatusFilter(request=None,
                                         params={'status': 'pago'},
                                         model=Transaction,
                                         model_admin=TransactionAdmin)
        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.get())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

    def test_order_full_name_search(self):
        from orders.models import Order

        OrderFactory.create_batch(5)
        user = UserFactory(
            name='Carolina Josefa Leopoldina de Habsburgo-Lorena')
        order = OrderFactory(student=user)

        result = Order.objects.filter(full_name__contains='josefa')
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.get())

    def tearDown(self):
        self.responses.__exit__()
