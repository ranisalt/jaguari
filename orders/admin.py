import os
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from .models import Degree, Order


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def birthday_tag(self, obj: Order):
        return obj.birthday.strftime('%d/%m/%Y')

    def cpf_tag(self, obj: Order):
        parts = (obj.cpf[i:i+3] for i in range(0, 11, 3))
        return '{}.{}.{}-{}'.format(*parts)

    def degree_tag(self, obj: Order):
        return '{} em {}'.format(obj.degree.get_tier_display(), obj.degree.name)

    degree_tag.short_description = _('Academic degree')

    def name_tag(self, obj: Order):
        return obj.student.get_full_name()

    def identity(self, obj: Order):
        return '{} {}/{}'.format(obj.identity_number,
                                 obj.identity_issuer,
                                 obj.identity_state)

    picture_html = '<img src="{}" style="max-height:200px; max-width:200px;"/>'

    def picture_tag(self, obj: Order):
        if obj.picture:
            return mark_safe(
                self.picture_html.format(
                    os.path.join('/', settings.MEDIA_URL, obj.picture.url)
                ))

    list_display = ('name_tag', 'created_at', 'print_status')
    fields = ('use_code',
              'name_tag',
              'birthday_tag',
              'cpf_tag',
              'identity',
              'enrollment_number',
              'degree_tag',
              'picture_tag',
              'print_status')
    readonly_fields = ('name_tag',
                       'birthday_tag',
                       'cpf_tag',
                       'identity',
                       'enrollment_number',
                       'degree_tag',
                       'picture_tag')
