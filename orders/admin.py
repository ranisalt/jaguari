from django.contrib import admin
from django.db.models.expressions import F as Field
from django.db.models.expressions import Func, Value
from django.utils.translation import ugettext_lazy as _
from pagseguro.models import Transaction

from .models import Degree, Order


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tier', 'name', 'alias', 'campus')
    list_filter = ('tier', 'campus')
    fields = ('id', 'tier', 'name', 'alias', 'campus')
    readonly_fields = ('id', 'tier', 'name', 'campus')


strip_uuid = Func(Field('reference'), Value('-'), Value(''), function='REPLACE')


class TransactionStatusFilter(admin.SimpleListFilter):
    title = _('transaction status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('none', _('No transaction')),
            ('pending', _('Pending')),
            ('available', _('Available')),
            ('unavailable', _('Unavailable'))
        )

    def queryset(self, request, queryset):
        if not self.value():
            return

        transactions = Transaction.objects.annotate(order_id=strip_uuid)

        if self.value() == 'pending':
            lookups = ['aguardando', 'em_analise']

        elif self.value() == 'available':
            lookups = ['pago', 'disponivel']

        elif self.value() == 'unavailable':
            lookups = ['em_disputa', 'devolvido', 'cancelado']

        else:  # self.value() == 'none'
            return queryset.exclude(id__in=transactions.values('order_id'))

        inner_qs = transactions.filter(status__in=lookups).values('order_id')
        return queryset.filter(id__in=inner_qs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = []
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super(OrderAdmin, self).get_queryset(request)
        return qs.exclude(picture='')

    def birthday_tag(self, obj: Order):
        return obj.get_birthday_display()

    birthday_tag.short_description = _('birthday')

    def cpf_tag(self, obj: Order):
        return obj.get_cpf_display()

    cpf_tag.short_description = _('CPF')

    def name_tag(self, obj: Order):
        return obj.student.get_full_name()

    name_tag.short_description = _('name')

    def identity_tag(self, obj: Order):
        return obj.get_rg_display()

    identity_tag.short_description = _('identity')

    def degree_tag(self, obj: Order):
        return obj.get_degree_display()

    degree_tag.short_description = _('academic degree')

    def template_tag(self, obj: Order):
        from django.urls import reverse
        from django.utils.html import format_html

        if not obj.picture or not obj.use_code:
            return

        tag = ('<object data="{0}" type="image/svg+xml"></object>'
               '<a style="display: block" href="{0}?background=false">{1}</a>')
        return format_html(tag, reverse('orders:detail', kwargs={
            'pk': str(obj.pk),
        }), _('Click here to download printable template'))

    template_tag.short_description = _('template')

    def transaction_tag(self, obj: Order):
        transaction = Transaction.objects.get(reference=str(obj.pk))
        if transaction:
            return transaction.get_status_display()

    transaction_tag.empty_value_display = _('(none)')
    transaction_tag.short_description = _('transaction status')

    list_display = ('name_tag', 'created_at', 'transaction_tag', 'print_status')
    list_filter = (TransactionStatusFilter,
                   'degree__tier',
                   'degree__campus',
                   'print_status')
    search_fields = ('student__first_name', 'student__last_name')
    fields = ('use_code',
              'name_tag',
              'birthday_tag',
              'cpf_tag',
              'identity_tag',
              'enrollment_number',
              'degree_tag',
              'template_tag',
              'transaction_tag',
              'print_status')
    readonly_fields = ('name_tag',
                       'birthday_tag',
                       'cpf_tag',
                       'identity_tag',
                       'enrollment_number',
                       'degree_tag',
                       'template_tag',
                       'transaction_tag')
