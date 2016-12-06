from django.contrib import admin
from .models import Degree, Order


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def picture_tag(self):
        import os
        from django.utils.safestring import mark_safe
        return mark_safe('<img src="{}" />'.format(
            os.path.join(settings.MEDIA_ROOT, self.picture)
        ))

    list_display = ['student', 'picture_tag']
