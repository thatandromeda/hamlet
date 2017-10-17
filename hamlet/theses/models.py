import re

from django.contrib.postgres.fields import ArrayField
from django.db import models


class Person(models.Model):
    # NOTE: distinct people with the same name may be stored as the same Person
    # instance, because we have no way to disambiguate.
    name = models.CharField(max_length=75)

    @staticmethod
    def handle_special_cases(namestring):
        # Fix specific authors with wonky metadata not captured by other rules.
        namestring = namestring.replace('Ren, Xiaoyuan, S.M. (Xiaoyuan Charlene) Massachusetts Institute of Technology',  # noqa
            'Ren, Xiaoyuan (Xiaoyuan Charlene)'
            ).replace('Stanford, Joseph, S.M. (Joseph Marsh) Massachusetts Institute of Technology',  # noqa
            'Stanford, Joseph (Joseph Marsh)'
            ).replace('Wang, Zhiyong, S.M. Massachusetts Institute of Technology. Engineering Systems Division',  # noqa
            'Wang, Zhiyong'
            ).replace('Williams, Christina M., M.B.A. (Christina Marie). Massachusetts Institute of Technology',  # noqa
            'Williams, Christina M. (Christina Marie)')

        return namestring

    @staticmethod
    def clean_metadata(namestring):
        """Extract a list of author names out of raw metadata strings.

        Breaking apart authors/advisors into separate Person instances is
        better than storing them in an ArrayField because ArrayField only
        supports searching for entire tokens, whereas with CharField we can
        use icontains to search for substrings."""

        namestring = Person.handle_special_cases(namestring)

        # Split on " and " - sometimes there are multiple authors given in a
        # string.
        names = namestring.split(' and ')

        # Remove degrees.
        degrees = [', S.M. Massachusetts Institute of Technology',
                   ', M. Eng. Massachusetts Institute of Technology',
                   ', Ph. D. Massachusetts Institute of Technology',
                   ', Nav.E. Massachusetts Institute of Technology',
                   ', Nav. E. Massachusetts Institute of Technology',
                   ', M.B.A. Massachusetts Institute of Technology']

        for deg in degrees:
            names = [name.replace(deg, '') for name in names]

        # Strip leading & trailing whitespace.
        names = [name.strip() for name in names]

        # Strip trailing periods, except when part of "Jr." or an initial.
        names = [re.sub('(?<!( [A-Z]|Jr)).$', '', name) for name in names]

        return names


class Department(models.Model):
    # Anticipates things like "Department of Mathematics", not "Course 18".
    name = models.CharField(max_length=255)
    # See http://catalog.mit.edu/subjects/#bycoursenumbertext . Add these by
    # hand after initializing the database. Some historical departments may not
    # have course numbers. Some programs do not have a name of the form
    # "Course X" but instead have acronyms, so the course field has to allow
    # for "Course" to be written in, not assume it can be prefixed.
    course = models.CharField(max_length=10, blank=True)

    @staticmethod
    def clean_metadata(deptstring):
        deptstring = deptstring.replace(
            'Massachusetts Institute of Technology.', '').strip()

    @staticmethod
    def create_from_metadata(metadata):
        clean = Department.clean_metadata(metadata)
        if not Department.objects.filter(name=clean):
            Department.objects.create(name=clean)


class Thesis(models.Model):
    # Max length observed by sampling in the wild is 183; 255 is max length
    # guaranteed to be supported by CharField.
    # It would be great to use CICharField here, but we need superuser
    # privileges to set up the database for it, so deploying it to Heroku is a
    # no-go.
    title = models.CharField(max_length=255)
    author = models.ManyToManyField(Person, related_name='theses_written')
    advisor = models.ManyToManyField(Person, related_name='theses_advised')
    department = models.ManyToManyField(Department)
    degree = models.CharField(max_length=10)  # SB, M. Eng., etc.
    url = models.URLField()
    # Not DateField, because we only have year, not month or day. Storing as an
    # integer rather than a string should allow for comparisons to happen in
    # the expected way. This is the copyright date, NOT the accessioning or
    # availability dates, which may be quite different.
    year = models.IntegerField()
    # Thesis set is amenable to ArrayField because it's a controlled
    # vocabulary and there's no reason to search for anything other than a
    # complete token (e.g. 'hdl_1721.1_7681').
    sets = ArrayField(models.CharField(max_length=17))
