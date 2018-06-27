import re

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from hamlet.citations.extract_refs import extract_good_refs
from hamlet.citations.models import Citation
from hamlet.theses.models import Thesis


class Command(BaseCommand):
    help = 'Processes citations from theses and adds to the database'

    def add_arguments(self, parser):
        parser.add_argument('maxfiles', type=int)

    def handle(self, *args, **options):
        start_time = now()

        maxfiles = options['maxfiles']
        pattern = re.compile('1721.1\-(\d+)\.txt')
        base_fields = Citation._meta.get_fields()
        fields = [f.name for f in base_fields
                  if f.name not in ['thesis', 'raw_ref', 'id']]

        good = extract_good_refs(maxfiles)

        total_attempts = 0
        total_created = 0

        for handle, refs in good.items():
            identifier = pattern.match(handle).group(1)
            t = Thesis.objects.get(identifier=identifier)

            for item in refs:
                total_attempts += 1
                raw_ref = item.get('raw_ref')
                if not raw_ref:
                    continue

                # raw_ref is produced as a one-element list instead of a string.
                raw_ref = raw_ref[0]

                # Strip off any reference numbers left over from the
                # bibliography.
                raw_ref = re.sub(r'^\[\d+\] ', '', raw_ref)

                c, _ = Citation.objects.get_or_create(thesis=t,
                        raw_ref=raw_ref)
                for field in fields:
                    value = item.get(field)

                    # Save blanks, not nulls.
                    if not value:
                        value = ''
                    else:
                        value = value[0]

                    setattr(c, field, value)

                try:
                    c.save()
                    total_created += 1
                except:
                    print('FAIL')
                    for field in fields:
                        value = item.get(field)
                        print(field)
                        print(value)

        end_time = now()
        elapsed = (end_time - start_time).seconds

        self.stdout.write(
            self.style.SUCCESS(' %d citations created' % total_created))
        self.stdout.write(
            self.style.SUCCESS('%d seconds elapsed' % elapsed))
