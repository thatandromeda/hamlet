from django.contrib import admin

from .models import Thesis, Person, Department, Contribution


class ContributionInline(admin.TabularInline):
    model = Contribution


class ThesisAdmin(admin.ModelAdmin):
    inlines = (ContributionInline,)
    list_filter = ('department', 'degree')
    search_fields = ('contribution__person__name',
                     'department__course',
                     'identifier',
                     'title')


class PersonAdmin(admin.ModelAdmin):
    def theses_written(self, obj):
        return Thesis.objects.filter(
            contribution__role=Contribution.AUTHOR,
            contribution__person=obj).count()

    def theses_advised(self, obj):
        return Thesis.objects.filter(
            contribution__role=Contribution.ADVISOR,
            contribution__person=obj).count()

    list_display = ('name', 'theses_written', 'theses_advised')
    search_fields = ('name',)


admin.site.register(Thesis, ThesisAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Department, admin.ModelAdmin)
