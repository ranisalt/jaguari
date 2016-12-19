import os
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from .models import Degree, Order


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tier', 'name', 'campus')
    list_filter = ('tier', 'campus')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = None
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super(OrderAdmin, self).get_queryset(request)
        return qs.exclude(picture='')

    def birthday_tag(self, obj: Order):
        return obj.formatted_birthday()

    birthday_tag.short_description = _('birthday')

    def cpf_tag(self, obj: Order):
        return obj.formatted_cpf()

    cpf_tag.short_description = _('CPF')

    def name_tag(self, obj: Order):
        return obj.student.get_full_name()

    name_tag.short_description = _('name')

    def identity_tag(self, obj: Order):
        return obj.formatted_rg()

    identity_tag.short_description = _('identity')

    def degree_tag(self, obj: Order):
        obj.formatted_degree()

    degree_tag.short_description = _('academic degree')

    picture_html = '<img src="{}" style="max-height:200px; max-width:200px;"/>'

    def picture_tag(self, obj: Order):
        if obj.picture:
            return mark_safe(
                self.picture_html.format(
                    os.path.join('/', settings.MEDIA_URL, obj.picture.url)
                ))

    picture_tag.empty_value_display = _('(none)')
    picture_tag.short_description = _('picture')

    list_display = ('name_tag', 'created_at', 'print_status')
    list_filter = ('degree__tier', 'degree__campus', 'print_status')
    fields = ('use_code',
              'name_tag',
              'birthday_tag',
              'cpf_tag',
              'identity_tag',
              'enrollment_number',
              'degree_tag',
              'picture_tag',
              'print_status')
    readonly_fields = ('name_tag',
                       'birthday_tag',
                       'cpf_tag',
                       'identity_tag',
                       'enrollment_number',
                       'degree_tag',
                       'picture_tag')
