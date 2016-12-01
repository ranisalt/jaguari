import os
import responses
from six.moves.urllib import request
from unittest.mock import Mock
from django.conf import settings
from django.contrib.auth.models import User
from django.http.request import HttpRequest
from django.test import Client, TestCase
from .models import Order


def resource(name: str):
    return open(os.path.join(settings.BASE_DIR, 'tests', name), mode='rb')


degree = {
    "codigo": 208,
    "nome": "CIÊNCIAS DA COMPUTAÇÃO",
    "centro": "CTC",
    "permiteExtra": False,
    "departamento": {
        "codigo": "INE"
    },
    "situacao": {
        "id": 0
    },
    "nomeCompleto": "Ciências da Computação",
    "descricao": "O Curso de Ciências da Computação forma profissionais com "
                 "capacidade para utilizar e desenvolver novas tecnologias. "
                 "Nas primeiras fases, o currículo oferece disciplinas "
                 "teóricas com os fundamentos da computação: Matemática, "
                 "Eletrônica Geral, Sistemas Digitais, Redes de Computadores, "
                 "Sistemas Operacionais, Engenharia de Software, Computação "
                 "Gráfica e Programação.  \n \nO aluno estuda as tecnologias "
                 "mais recentes em disciplinas optativas. Uma das "
                 "peculiaridades do curso é a constante atualização do "
                 "currículo. Isso ocorre porque sempre que há uma novidade na "
                 "computação é criada uma optativa para que os estudantes "
                 "conheçam essa nova tecnologia. Outras características são a "
                 "grande quantidade de laboratórios e as numerosas pesquisas "
                 "das quais os graduandos participam em conjunto com "
                 "pós-graduandos.  \n \nTodos os alunos da UFSC têm acesso "
                 "gratuito à Internet, mas os estudantes de Ciências da "
                 "Computação têm vantagens: como dispõem de linhas especiais, "
                 "o acesso é mais rápido. \n \nNo mercado de trabalho da "
                 "área, nos próximos dez anos, não deve faltar emprego. "
                 "Devido à carência de profissionais, várias empresas de todo "
                 "o Brasil procuram os formandos da UFSC. A atuação se dá "
                 "geralmente em empresas de desenvolvimento de novas "
                 "tecnologias, telecomunicações, institutos de pesquisa e "
                 "universidades. Os professores do curso alertam para um "
                 "engano freqüente, confundir a função do bacharel em "
                 "Ciências da Computação com as desempenhadas pelo bacharel "
                 "em Sistemas de Informação. O profissional de Ciências da "
                 "Computação produz e desenvolve novas tecnologias, "
                 "como plataformas, software, interfaces. Quem é formado em "
                 "Sistemas de Informação aplica as inovações tecnológicas já "
                 "desenvolvidas. \n",
    "semestreCorrente": 20162,
    "campus": {
        "id": 1,
        "nome": "Campus Universitário  Reitor João David Ferreira Lima",
        "sigla": "UFSC/FLO"
    },
    "numeroVagas": 400,
    "numeroVagasPrimeiroSemestre": 50,
    "repositorioTCC": "7444"
}

student = [
    {
        "ativo": True,
        "id": "13100000",
        "idPessoa": 100000000400000,
        "codigoVinculo": 1,
        "nomeVinculo": "Aluno de Graduação",
        "matricula": 13100000,
        "codigoCurso": 208,
        "nomeCurso": "CIÊNCIAS DA COMPUTAÇÃO",
        "nome": "John Doe",
        "dataNascimento": "1990-01-01T00:00:00-03:00",
        "cpf": 26063723102,
        "identidade": "389372869",
        "codigoUfIdentidade": "SP",
        "siglaOrgaoEmissorIdentidade": "SSP",
        "codigoSituacao": 0,
        "nomeSituacao": "regular"
    }
]


class Requests(TestCase):
    def setUp(self):
        request.urlopen = Mock(side_effect=[resource('login.xml')])

        req = HttpRequest()
        req.session = {}

        self.client = Client()
        self.client.login(ticket='ST-b91d310a-6d50-45a3-9a1c-1c36fa135ab3',
                          service='http://localhost/?next=%2Forders%2Fnew%2F',
                          request=req)

        try:
            self.user = User.objects.get()
        except User.DoesNotExist:  # pragma: no cover
            self.user = User.objects.create_user(username='100000000400000')

    def test_new_order(self):
        self.assertEqual(Order.objects.count(), 0)

        with responses.RequestsMock() as r:
            r.add(responses.GET,
                  'https://ws.ufsc.br/CAGRService/cursoGraduacaoAluno/13100000',
                  json=degree)
            r.add(responses.GET,
                  'https://ws.ufsc.br/CadastroPessoaService'
                  '/vinculosPessoaById/100000000400000',
                  json=student)
            self.client.get('/orders/new/', follow=True)

        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        self.assertEqual(order.student, self.user)

    def test_post_order(self):
        self.assertEqual(Order.objects.count(), 0)

        with responses.RequestsMock() as r:
            r.add(responses.GET,
                  'https://ws.ufsc.br/CAGRService/cursoGraduacaoAluno/13100000',
                  json=degree)
            r.add(responses.GET,
                  'https://ws.ufsc.br/CadastroPessoaService'
                  '/vinculosPessoaById/100000000400000',
                  json=student)
            self.client.get('/orders/new/', follow=True)

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()

        res = self.client.post('/orders/new/')
        self.assertEqual(res.status_code, 302)
