from django.contrib import admin

from .models import Thesis, Person, Department, Contribution


class ContributionInline(admin.TabularInline):
    model = Contribution


class ThesisAdmin(admin.ModelAdmin):
    inlines = (ContributionInline,)


admin.site.register(Thesis, ThesisAdmin)
admin.site.register(Person, admin.ModelAdmin)
admin.site.register(Department, admin.ModelAdmin)
