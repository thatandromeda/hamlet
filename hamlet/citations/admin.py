from django.contrib import admin

from .models import Citation


class CitationAdmin(admin.ModelAdmin):
    model = Citation
    search_fields = ('author', 'year', 'doi', 'thesis__title', 'raw_ref')
    list_display = ('thesis', 'raw_ref')


admin.site.register(Citation, CitationAdmin)
