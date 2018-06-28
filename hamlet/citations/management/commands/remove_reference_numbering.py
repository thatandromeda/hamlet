import re

from django.core.management.base import BaseCommand

from hamlet.citations.models import Citation


class Command(BaseCommand):
    help = 'Removes reference numbers from the beginnings of citations'

    def handle(self, *args, **options):
        for c in Citation.objects.all():
            if re.match(r'\d+\.', c.raw_ref):
                c.raw_ref = re.sub(r'^\d+\. ', '', c.raw_ref).lstrip()
                c.save()
            if re.match(r'\[\d+\].', c.raw_ref):
                c.raw_ref = re.sub(r'\[\d+\].', '', c.raw_ref).lstrip()
                c.save()
            if re.match(r'\[\d+\]', c.raw_ref):
                c.raw_ref = re.sub(r'\[\d+\]', '', c.raw_ref).lstrip()
                c.save()
