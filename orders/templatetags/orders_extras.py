from django import template
from django.utils.translation import ugettext_lazy as _
from ..models import Degree

register = template.Library()


def cpf(value):
    raw = value['cpf']
    *parts, verifier = [raw[i:i + 3] for i in range(0, 11, 3)]
    return f'{".".join(parts)}-{verifier}'


def rg(value):
    number = value['identity_number']
    issuer = value['identity_issuer']
    state = value['identity_state']
    return f'{number} {issuer}/{state}'


def degree(value):
    degree = Degree.objects.get(pk=value)
    tier = degree.get_tier_display()
    name = degree.get_common_name()
    campus = degree.get_campus_display()
    return _('{tier} in {name} ({campus})').format(tier=tier,
                                                   name=name,
                                                   campus=campus)


register.filter('cpf', cpf)
register.filter('rg', rg)
register.filter('degree', degree)
