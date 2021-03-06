import uuid
from urllib.parse import urlunparse

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_cas_ng.signals import cas_user_authenticated
from django_localflavor_br.br_states import STATE_CHOICES


class DegreeManager(models.Manager):
    def get_or_fetch(self, pk, enrollment_hint):
        try:
            return self.get(pk=pk)
        except Degree.DoesNotExist:
            endpoint = urlunparse(('https', 'ws.ufsc.br', '/'.join([
                'CAGRService', 'cursoGraduacaoAluno', enrollment_hint
            ]), '', '', ''))
            response = requests.get(endpoint, auth=settings.CAGR_KEY).json()

            return self.create(id=response['codigo'],
                               tier=Degree.UNDERGRADUATE,
                               name=response['nomeCompleto'],
                               campus=response['campus']['id'])


class Degree(models.Model):
    HIGHER = 1
    UNDERGRADUATE = 2
    POSTGRADUATE = 3
    DEGREE_LEVEL_CHOICES = (
        (HIGHER, _('High school')),
        (UNDERGRADUATE, _('Undergraduate')),
        (POSTGRADUATE, _('Postgraduate')),
    )

    FLO = 1
    JOI = 2
    CBS = 3
    ARA = 4
    BLN = 5
    CAMPI_CHOICES = (
        (FLO, 'Florianópolis'),
        (JOI, 'Joinville'),
        (CBS, 'Curitibanos'),
        (ARA, 'Araranguá'),
        (BLN, 'Blumenau'),
    )

    id = models.IntegerField(editable=False,
                             primary_key=True,
                             verbose_name=_('id'))
    tier = models.SmallIntegerField(blank=False,
                                    choices=DEGREE_LEVEL_CHOICES,
                                    editable=False,
                                    verbose_name=_('tier'))
    name = models.CharField(editable=False,
                            max_length=127,
                            verbose_name=_('name'))
    alias = models.CharField(blank=True,
                             max_length=127,
                             null=True,
                             verbose_name=_('alias'))
    campus = models.SmallIntegerField(choices=CAMPI_CHOICES, editable=False)

    def get_common_name(self):
        return self.alias if self.alias is not None else self.name

    def __str__(self):  # pragma: no cover
        return f'{self.get_common_name()} ({self.pk})'

    class Meta:
        verbose_name = _('degree')

    objects = DegreeManager()


@receiver(cas_user_authenticated)
def user_authenticated(user, attributes, **kwargs):
    user.email = attributes['email']
    name = attributes['nomeSocial']
    middle = name.rfind(' ', 0, 30)
    user.first_name, user.last_name = name[:middle], name[middle:].lstrip()
    user.save()


class MissingFieldsError(KeyError):
    def __init__(self, fields, *args, **kwargs):
        self.fields = fields
        super().__init__(*args, **kwargs)


class NoValidLinkError(ValueError):
    pass


class OrderManager(models.Manager):
    required_fields = {
        'codigoCurso': _('degree'),
        'codigoUfIdentidade': _('identity state'),
        'cpf': _('CPF'),
        'dataNascimento': _('birthday'),
        'id': _('enrollment number'),
        'identidade': _('identity number'),
        'siglaOrgaoEmissorIdentidade': _('identity issuer'),
    }

    def get_queryset(self):
        return super(OrderManager, self).get_queryset().annotate(
            full_name=Concat('student__first_name',
                             Value(' '),
                             'student__last_name'))

    def fetch(self, user):
        def is_valid(ativo, codigoSituacao, codigoVinculo, **kwargs):
            """
            codigoSituacao == 0 means regular student
            codivoVinculo == 1 means undergraduate
            """
            return ativo and codigoSituacao == 0 and codigoVinculo == 1

        endpoint = urlunparse(('https', 'ws.ufsc.br', '/'.join([
            'CadastroPessoaService', 'vinculosPessoaById', user.get_username()
        ]), '', '', ''))
        response = requests.get(endpoint, auth=settings.CAGR_KEY).json()

        links = [link for link in response if is_valid(**link)]
        if len(links) == 0:
            raise NoValidLinkError()

        *_, data = links
        missing = [f for f in self.required_fields if f not in data]
        if len(missing) > 0:
            raise MissingFieldsError(self.required_fields[f] for f in missing)

        degree_id, enrollment_number = data['codigoCurso'], data['id']
        degree = Degree.objects.get_or_fetch(degree_id, enrollment_number)
        return dict(student_id=user.pk,
                    degree_id=degree.pk,
                    birthday=data['dataNascimento'],
                    cpf=str(data['cpf']).zfill(11),
                    identity_number=data['identidade'],
                    identity_issuer=data['siglaOrgaoEmissorIdentidade'],
                    identity_state=data['codigoUfIdentidade'],
                    enrollment_number=enrollment_number)


def picture_path(instance, filename: str) -> str:
    import os
    head, tail = os.path.split(filename)
    root, ext = os.path.splitext(tail)
    return os.path.join(head, ''.join([str(instance.pk), ext]))


class Order(models.Model):
    NOT_READY = 0
    REGISTERED = 3
    READY = 1
    DELIVERED = 2
    PRINT_STATUS_CHOICES = (
        (NOT_READY, _('Waiting')),
        (REGISTERED, _('Registered')),
        (READY, _('Printed')),
        (DELIVERED, _('Delivered')),
    )

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    use_code = models.CharField(max_length=8, verbose_name=_('use code'))
    student = models.ForeignKey(User, editable=False, on_delete=models.PROTECT)
    degree = models.ForeignKey(Degree, editable=False, on_delete=models.PROTECT)
    birthday = models.DateField(editable=False)
    cpf = models.CharField(max_length=11, editable=False)
    identity_number = models.TextField(editable=False)
    identity_issuer = models.TextField(editable=False)
    identity_state = models.CharField(choices=STATE_CHOICES,
                                      editable=False,
                                      max_length=2)
    enrollment_number = models.TextField(editable=False,
                                         verbose_name=_('enrollment number'))
    picture = models.ImageField(blank=True, upload_to=picture_path)
    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False,
                                      verbose_name=_('created at'))
    print_status = models.SmallIntegerField(choices=PRINT_STATUS_CHOICES,
                                            default=NOT_READY,
                                            verbose_name=_('print status'))

    def get_birthday_display(self):
        return self.birthday.strftime('%d/%m/%Y')

    def get_cpf_display(self):
        *parts, verifier = [self.cpf[i:i + 3] for i in range(0, 11, 3)]
        return f'{".".join(parts)}-{verifier}'

    def get_degree_display(self):
        tier = self.degree.get_tier_display()
        name = self.degree.get_common_name()
        campus = self.degree.get_campus_display()
        return _('{tier} in {name} ({campus})').format(tier=tier,
                                                       name=name,
                                                       campus=campus)

    def get_rg_display(self):
        number = self.identity_number
        issuer = self.identity_issuer
        state = self.identity_state
        return f'{number} {issuer}/{state}'

    def __str__(self):  # pragma: no cover
        return '{self.student.get_full_name()} ({self.pk})'

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')

    objects = OrderManager()


@receiver(models.signals.post_delete, sender=Order)
def post_delete(sender, instance: Order, **kwargs):
    import os
    if instance.picture and os.path.isfile(instance.picture.path):
        os.remove(instance.picture.path)
