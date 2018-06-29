import string

from django.core.management.base import BaseCommand

from hamlet.citations.models import Citation


class Command(BaseCommand):
    help = 'Deletes citations which are probably garbage'
    citation_fields = Citation._meta.get_fields()

    def _percentage_nonpunctuation(self, mystring):
        '''
        Returns the % of mystring which is not punctuation (expressed as
        a decimal between 0 and 1).
        '''
        # The string with all its punctuation removed.
        nonpunc = mystring.translate(str.maketrans('', '', string.punctuation))

        return len(nonpunc) / len(mystring)

    def _percentage_lowercase(self, mystring):
        '''
        Returns the % of mystring which is not capital letters (expressed as
        a decimal between 0 and 1).

        Technically this isn't the same as being lowercase (characters could be
        digits or spaces), but it's less confusing to write into inequalities
        than "_percentage_noncapital".
        '''
        # The string with all its capitals removed.
        lowercase = mystring.translate(
            str.maketrans('', '', string.ascii_uppercase))

        return len(lowercase) / len(mystring)

    def _nonempty_field_count(self, citation):
        '''
        Returns the number of nonempty fields in a citation. (Should always
        be at least 2 - raw_ref and thesis.)
        '''
        return len([x for x in self.citation_fields
                    if getattr(citation, x.name)])

    def handle(self, *args, **options):
        orig_count = Citation.objects.count()
        deleted = 0
        loopcount = 0
        for c in Citation.objects.all()[0:orig_count]:
            # Things with too high a percentage of punctuation are probably
            # equations or figure captions or tables. Things with too little
            # punctuation can't be well-formed citations.
            nonpunct = self._percentage_nonpunctuation(c.raw_ref)
            if nonpunct < 0.8 or nonpunct > 0.98:
                c.delete()
                deleted += 1
                continue

            # Things with too high a percentage of lowercase letters are
            # probably text fragments not caught by the previous check -
            # but they may also be citations containing URLs (which, unlike
            # journal and article titles, tend to be entirely lowercase).
            lowercase = self._percentage_lowercase(c.raw_ref)
            if lowercase > 0.97 and 'http' not in c.raw_ref:
                c.delete()
                deleted += 1
                continue

            # Things with too low a percentage of lowercase letters are also
            # garbage - figure captions, OCR errors, etc. However, this
            # percentage must be quite low, because some people put author
            # names in all caps.
            if lowercase < 0.6:
                c.delete()
                deleted += 1
                continue

            # These are equations, figures, etc.
            if any([
                '>' in c.raw_ref,
                '<' in c.raw_ref,
                '%' in c.raw_ref
            ]) and 'http' not in c.raw_ref:
                c.delete()
                deleted += 1
                continue

            # Random garbage
            if all([
                c.raw_ref[0] not in string.ascii_uppercase,
                c.raw_ref[0] != '"',
                self._nonempty_field_count(c) < 4
            ]):
                c.delete()
                deleted += 1
                continue

            # Remaining citations are probably mostly okay. They may be
            # fragmentary, but that's still useful; people can likely still
            # track them down.

            # Progress indicator
            loopcount += 1
            if loopcount % 100 == 0:
                self.stdout.write(self.style.WARNING(
                    '%d citations processed' % loopcount))
                self.stdout.write(self.style.WARNING(
                    '%d citations deleted' % deleted))

        self.stdout.write(
            self.style.NOTICE(' %d citations deleted' % deleted))
        self.stdout.write(
            self.style.SUCCESS('%d citations remain' % (orig_count - deleted)))
