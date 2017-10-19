from django.contrib import admin

from .models import Thesis


class ThesisAdmin(admin.ModelAdmin):
    pass


admin.site.register(Thesis, ThesisAdmin)
