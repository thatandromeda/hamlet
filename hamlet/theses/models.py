from functools import reduce
import pickle
import re

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property


class Person(models.Model):
    # NOTE: distinct people with the same name may be stored as the same Person
    # instance, because we have no way to disambiguate.
    name = models.CharField(max_length=75)

    def __str__(self):
        return self.name

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
                'Williams, Christina M. (Christina Marie)'
            ).replace('Lu, Xin. Ph. D. Massachusetts Institute of Technology. Department of Materials Science and Engineering',  # noqa
                'Lu, Xin'
            ).replace('Rodriguez, Miguel A. (Miguel Angel), M.C.P. Massachusetts Institute of Technology',  # noqa
                'Rodriguez, Miguel A. (Miguel Angel)'
            )

        return namestring

    @staticmethod
    def clean_metadata(namestring):
        """Extract a list of personal names out of raw metadata strings.

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
                   ', M.B.A. Massachusetts Institute of Technology',
                   ' Massachusetts Institute of Technology']

        for deg in degrees:
            names = [name.replace(deg, '') for name in names]

        # Strip leading & trailing whitespace.
        names = [name.strip() for name in names]

        return names

    class Meta:
        ordering = ['name']


class Department(models.Model):
    # Anticipates things like "Department of Mathematics", not "Course 18".
    name = models.CharField(max_length=255)
    # See http://catalog.mit.edu/subjects/#bycoursenumbertext . Add these by
    # hand after initializing the database. Some historical departments may not
    # have course numbers. Some programs do not have a name of the form
    # "Course X" but instead have acronyms, so the course field has to allow
    # for "Course" to be written in, not assume it can be prefixed.
    course = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def clean_metadata(deptstring):
        deptstring = deptstring.replace(
            'Massachusetts Institute of Technology.', ''
        ).replace(
            'Dept. of', 'Department of'
        ).strip().rstrip('.')
        return deptstring

    @staticmethod
    def get_or_create_from_metadata(metadata):
        print(metadata)
        clean = Department.clean_metadata(metadata)
        print(clean)
        dept, _ = Department.objects.get_or_create(name=clean)
        return dept

    class Meta:
        ordering = ['name']


class Thesis(models.Model):
    REPLS = (('E.E', 'Elec.E'), ('Elect.E', 'Elec.E'), ('OceanE', 'Ocean.E'),
             ('M.ArchAS', 'M.Arch.A.S'), ('PhD', 'Ph.D'), ('ScD', 'Sc.D'))

    DEGREES = ['B.Arch.', 'B.C.P.', 'B.S.', 'C.P.H.', 'Chem.E.', 'Civ.E.',
               'E.A.A.', 'Elec.E.', 'Env.E.', 'M.Arch.', 'M.Arch.A.S.',
               'M.B.A.', 'M.C.P.', 'M.Eng.', 'M.Fin.', 'M.S.', 'M.S.V.S.',
               'Mat.Eng.', 'Nav.Arch.', 'Mech.E.', 'Nav.E.', 'Nucl.E.',
               'Ocean.E.', 'Ph.D.', 'S.B.', 'S.M.', 'S.M.M.O.T.', 'Sc.D.']

    # Max length observed by sampling in the wild is 183; 255 is max length
    # guaranteed to be supported by CharField.
    # It would be great to use CICharField here, but we need superuser
    # privileges to set up the database for it, so deploying it to Heroku is a
    # no-go.
    title = models.TextField()
    contributor = models.ManyToManyField(Person, through='Contribution')
    department = models.ManyToManyField(Department)
    degree = models.CharField(max_length=20)  # SB, M. Eng., etc.
    url = models.URLField()
    # Not DateField, because we only have year, not month or day. Storing as an
    # integer rather than a string should allow for comparisons to happen in
    # the expected way. This is the copyright date, NOT the accessioning or
    # availability dates, which may be quite different.
    year = models.IntegerField()
    identifier = models.IntegerField(unique=True, db_index=True,
        help_text='The part after the final slash in things '
            'like http://hdl.handle.net/1721.1/39504')
    unextractable = models.BooleanField(default=False,
        help_text='Will be set to True if attempts to extract text from '
            'the pdf failed; such theses are not part of the neural net, '
            'and cannot be used in data visualization.')
    # Contains the inferred vector for a document. Always needed for getting
    # neural net data on documents outside of the training set. Documents
    # inside the training set use their labels where possible, but cannot
    # always do so (e.g. if being compared to documents outside the training
    # set).
    # The inferred vector is a numpy array; we use pickle to serialize it into
    # bytes before storing it here. Access via the vector property, which
    # unpickles.
    _vector = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return self.title

    @cached_property
    def label(self):
        return '1721.1-{}.txt'.format(self.identifier)

    @cached_property
    def vector(self):
        return pickle.loads(self._vector)

    @cached_property
    def authors(self):
        contribs = Contribution.objects.filter(
            thesis=self, role=Contribution.AUTHOR)
        return Person.objects.filter(contribution__in=contribs)

    @cached_property
    def advisors(self):
        contribs = Contribution.objects.filter(
            thesis=self, role=Contribution.ADVISOR)
        return Person.objects.filter(contribution__in=contribs)

    @cached_property
    def dspace_url(self):
        return 'https://dspace.mit.edu/handle/1721.1/{id}'.format(
            id=self.identifier)

    # ~~~~~~~~~~~~~~~~~~~~~ Functions for metadata ingest ~~~~~~~~~~~~~~~~~~~~~

    def add_people(self, people, author=True):
        """Given a list of person name strings, add Person relations."""
        if author:
            role = Contribution.AUTHOR
        else:
            role = Contribution.ADVISOR

        for person in people:
            names = Person.clean_metadata(person)
            for name in names:
                if not self.contribution_set.filter(person__name=name,
                                                    role=role):
                    person, _ = Person.objects.get_or_create(name=name)
                    Contribution.objects.create(
                        person=person,
                        role=role,
                        thesis=self
                    )

    def add_departments(self, departments):
        for deptstring in departments:
            dept = Department.get_or_create_from_metadata(deptstring)
            self.department.add(dept)

    @classmethod
    def extract_degree(self, degree_statement):
        """Takes METS format metadata and finds degrees."""
        result = []
        try:
            degree = re.findall('[A-Z][a-z]{,4}\.? ?[A-Z][a-z]{,3}\.?[A-Z]?\.?'
                                '[A-Z]?\.?[A-Z]?\.?', degree_statement)
            for item in degree:
                i = item.replace(' ', '')
                i = i.rstrip('.')
                i = reduce(lambda a, kv: a.replace(*kv), self.REPLS, i)
                if not i.endswith('.'):
                    i += '.'
                if i in self.DEGREES:
                    result.append(i)
        except TypeError:
            result = None
        return result or None

    # ~~~~~~~~~~~~~~~~~ Functions for neural net interactions ~~~~~~~~~~~~~~~~~

    # See https://radimrehurek.com/gensim/models/doc2vec.html for affordances
    # offered by doc2vec.
    def get_most_similar(self, threshold=0.75, topn=50):
        """Find theses above a given similarity threshold. If there are more
        than topn, only the topn most similar will be returned (to a maximum
        of 50).

        Threshold defaults to 0.75, because in practice that seems to usually
        result in theses that humans find similar, but also a manageable number
        of results."""

        topn = min(topn, 50)
        friends = settings.NEURAL_NET.docvecs.most_similar(
            [self.label], topn=topn)

        friend_labels = [x[0] for x in friends if x[1] > threshold]
        friend_ids = [x.split('-')[1].split('.')[0] for x in friend_labels]
        return Thesis.objects.filter(identifier__in=friend_ids)

    def get_similarity(self, thesis):
        """Get the similarity between this and another thesis."""
        return settings.NEURAL_NET.docvecs.similarity(
            self.label, thesis.label)

    class Meta:
        verbose_name_plural = 'theses'


class Contribution(models.Model):
    AUTHOR = 'author'
    ADVISOR = 'advisor'

    ROLE_CHOICES = (
        (AUTHOR, AUTHOR),
        (ADVISOR, ADVISOR),
    )

    thesis = models.ForeignKey(Thesis)
    person = models.ForeignKey(Person)
    role = models.CharField(max_length=7, choices=ROLE_CHOICES)
