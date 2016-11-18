import iso8601
from .utils import make_request, random_use_code
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django_cas_ng.signals import cas_user_authenticated
from django_localflavor_br.br_states import STATE_CHOICES


class DegreeManager(models.Manager):
    def fetch(self, enrollment_hint):
        response = make_request(settings.CAGR_DEGREE_URL, enrollment_hint)

        return self.update_or_create(
            id=response['codigo'],
            tier=Degree.UNDERGRADUATE,
            name=response['nomeCompleto'],
        )


class Degree(models.Model):
    HIGHER = 1
    UNDERGRADUATE = 2
    MASTER = 3
    DOCTOR = 4
    DEGREE_LEVEL_CHOICES = (
        (HIGHER, 'Ensino Médio'),
        (UNDERGRADUATE, 'Graduação'),
        (MASTER, 'Mestrado'),
        (DOCTOR, 'Doutorado'),
    )
    id = models.IntegerField(primary_key=True)
    tier = models.SmallIntegerField(choices=DEGREE_LEVEL_CHOICES)
    name = models.CharField(max_length=63)

    objects = DegreeManager()

    def __str__(self):
        return "%s" % self.name


@receiver(cas_user_authenticated)
def user_authenticated(user, attributes, **kwargs):
    user.email = attributes['email']
    user.first_name, user.last_name = attributes['nomeSocial'].split(maxsplit=1)
    user.save()


class Order(models.Model):
    use_code = models.CharField(default=random_use_code, primary_key=True)
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    degree = models.ForeignKey(Degree, on_delete=models.PROTECT)
    birthday = models.DateField()
    cpf = models.CharField(max_length=11)
    identity_number = models.TextField()
    identity_issuer = models.TextField()
    identity_state = models.CharField(choices=STATE_CHOICES, max_length=2)
    enrollment_number = models.TextField()
    certificate = models.BinaryField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def fetch(cls, user):
        def is_valid(ativo, codigoSituacao, codigoVinculo, **kwargs):
            """
            codigoSituacao == 0 means regular student
            codivoVinculo == 1 means undergraduate
            """
            return ativo and codigoSituacao == 0 and codigoVinculo == 1

        response = make_request(settings.CAGR_INFO_URL, user.username)
        *_, data = (link for link in response if is_valid(**link))

        enrollment_number = data['matricula']
        degree, _ = Degree.objects.fetch(str(enrollment_number))
        birthday = iso8601.parse_date(data['dataNascimento'])
        return cls.objects.create(
            student=user,
            degree=degree,
            birthday=birthday.date(),
            cpf=str(data['cpf']).zfill(11),
            identity_number=data['identidade'],
            identity_issuer=data['siglaOrgaoEmissorIdentidade'],
            identity_state=data['codigoUfIdentidade'],
            enrollment_number=enrollment_number,
        )
