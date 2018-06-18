import factory
from django.contrib.auth.models import User
from django.utils import timezone
from pagseguro.models import Transaction
from .models import Degree, Order


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: str(10 ** 14 + n))
    name = factory.Faker('name')
    email = factory.Faker('email')

    @classmethod
    def _adjust_kwargs(cls, name: str, **kwargs):
        kwargs['first_name'], kwargs['last_name'] = name.split(maxsplit=1)
        return kwargs


class DegreeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Degree

    id = factory.Sequence(lambda n: str(n).zfill(3))
    tier = Degree.UNDERGRADUATE
    campus = factory.Iterator(x for (x, _) in Degree.CAMPI_CHOICES)


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    student = factory.SubFactory(UserFactory)
    degree = factory.SubFactory(DegreeFactory)
    birthday = factory.Faker('date_object')
    cpf = factory.Faker('numerify', text='###########')
    identity_number = factory.Faker('numerify', text='#######')
    identity_issuer = 'SSP'
    identity_state = 'SC'
    enrollment_number = factory.Faker('numerify', text='151#####')


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    code = factory.Faker('uuid4')
    status = 'aguardando'
    date = factory.LazyFunction(timezone.now)
    last_event_date = factory.LazyFunction(timezone.now)
