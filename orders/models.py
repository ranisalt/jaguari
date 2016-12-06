import iso8601
import requests
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django_cas_ng.signals import cas_user_authenticated
from django_localflavor_br.br_states import STATE_CHOICES


class DegreeManager(models.Manager):
    endpoint = 'https://ws.ufsc.br/CAGRService/cursoGraduacaoAluno/{}'

    def fetch(self, enrollment_hint):
        response = requests.get(self.endpoint.format(enrollment_hint)).json()

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


@receiver(cas_user_authenticated)
def user_authenticated(user, attributes, **kwargs):
    user.email = attributes['email']
    user.first_name, user.last_name = attributes['nomeSocial'].split(maxsplit=1)
    user.save()


class OrderManager(models.Manager):
    endpoint = 'https://ws.ufsc.br/CadastroPessoaService/vinculosPessoaById/{}'

    def fetch(self, user):
        def is_valid(ativo, codigoSituacao, codigoVinculo, **kwargs):
            """
            codigoSituacao == 0 means regular student
            codivoVinculo == 1 means undergraduate
            """
            return ativo and codigoSituacao == 0 and codigoVinculo == 1

        response = requests.get(self.endpoint.format(user.get_username()),
                                auth=settings.CAGR_CREDENTIALS)
        *_, data = (link for link in response.json() if is_valid(**link))

        enrollment_number = data['matricula']
        degree, _ = Degree.objects.fetch(str(enrollment_number))
        birthday = iso8601.parse_date(data['dataNascimento'])
        return self.create(
            student=user,
            degree=degree,
            birthday=birthday.date(),
            cpf=str(data['cpf']).zfill(11),
            identity_number=data['identidade'],
            identity_issuer=data['siglaOrgaoEmissorIdentidade'],
            identity_state=data['codigoUfIdentidade'],
            enrollment_number=enrollment_number,
        )


def picture_path(instance, filename: str) -> str:
    import os
    head, tail = os.path.split(filename)
    root, ext = os.path.splitext(tail)
    return os.path.join(head, ''.join([str(instance.pk), ext]))


class Order(models.Model):
    NOT_READY = 0
    READY = 1
    DELIVERED = 2
    PRINT_STATUS_CHOICES = (
        (NOT_READY, 'Aguardando'),
        (READY, 'Impresso'),
        (DELIVERED, 'Entregue'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    use_code = models.CharField(max_length=8, editable=False)
    student = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    degree = models.ForeignKey(Degree, on_delete=models.PROTECT, editable=False)
    birthday = models.DateField(editable=False)
    cpf = models.CharField(max_length=11, editable=False)
    identity_number = models.TextField(editable=False)
    identity_issuer = models.TextField(editable=False)
    identity_state = models.CharField(choices=STATE_CHOICES,
                                      max_length=2,
                                      editable=False)
    enrollment_number = models.TextField(editable=False)
    picture = models.ImageField(blank=True, upload_to=picture_path)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    print_status = models.SmallIntegerField(choices=PRINT_STATUS_CHOICES,
                                            default=NOT_READY)

    class Meta:
        ordering = ['-created_at']

    objects = OrderManager()
