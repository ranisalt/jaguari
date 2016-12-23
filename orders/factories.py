import factory
from django.contrib.auth.models import User
from .models import Degree, Order


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('numerify', text='100000000######')
    name = factory.Faker('name')
    email = factory.Faker('email')

    @classmethod
    def _adjust_kwargs(cls, name: str, **kwargs):
        kwargs['first_name'], kwargs['last_name'] = name.split(maxsplit=1)
        return kwargs


class DegreeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Degree

    id = factory.Faker('numerify', text='###')
    tier = Degree.UNDERGRADUATE
    campus = factory.Iterator(x for (x, _) in Degree.CAMPI_CHOICES)


class DegreeJSONFactory(factory.Factory):
    class Meta:
        model = dict

    codigo = factory.Faker('random_number', digits=3)
    nome = factory.LazyAttribute(lambda o: o.nomeCompleto.upper())
    centro = 'CTC'
    permiteExtra = False
    departamento = factory.Dict({'codigo': 'INE'})
    situacao = factory.Dict({'id': 0})
    nomeCompleto = factory.Faker('company')
    descricao = factory.Faker('text')
    semestreCorrente = 20162
    campus = factory.Dict({
        'id': factory.Iterator(x for (x, _) in Degree.CAMPI_CHOICES),
    })
    numeroVagas = factory.Faker('random_int', min=100, max=400)
    numeroVagasPrimeiroSemestre = factory.Faker('random_int', min=20, max=100)
    repositorioTCC = factory.Faker('numerify', text='####')


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    student = factory.SubFactory(UserFactory)
    degree = factory.SubFactory(DegreeFactory)
    birthday = factory.Faker('date_object')
    cpf = factory.Faker('random_number', digits=11)
    identity_number = factory.Faker('numerify', text='#######')
    identity_issuer = 'SC'
    identity_state = 'SSP'
    enrollment_number = factory.Faker('numerify', text='151#####')


class StudentJSONFactory(factory.Factory):
    class Meta:
        model = dict

    ativo = False
    id = factory.Faker('numerify', text='151#####')
    idPessoa = factory.Faker('numerify', text='100000000######')
    codigoVinculo = 1
    nomeVinculo = 'Aluno de Graduação',
    matricula = factory.LazyAttribute(lambda o: int(o.id))
    codigoCurso = factory.Faker('random_number', digits=3)
    nome = factory.Faker('name')
    dataNascimento = factory.Faker('iso8601')
    cpf = factory.Faker('random_number', digits=11)
    identidade = factory.Faker('numerify', text='#######')
    codigoUfIdentidade = 'SC'
    siglaOrgaoEmissorIdentidade = 'SSP'
    codigoSituacao = 0
    nomeSituacao = 'regular'

