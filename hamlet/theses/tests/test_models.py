from django.test import TestCase

from ..models import Person, Department, Thesis


class PersonTestCase(TestCase):
    fixtures = ['theses.json', 'departments.json', 'authors.json',
                'contributions.json']

    def test_clean_metadata_remove_degrees_1(self):
        base = 'Kofi Annan, S.M. Massachusetts Institute of Technology'
        self.assertEqual(['Kofi Annan'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_2(self):
        base = 'Somebody, M. Eng. Massachusetts Institute of Technology'
        self.assertEqual(['Somebody'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_3(self):
        base = 'Ronald McNair, Ph. D. Massachusetts Institute of Technology'
        self.assertEqual(['Ronald McNair'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_4(self):
        base = 'Boaty McBoatface, Nav. E. Massachusetts Institute of Technology'  # noqa
        self.assertEqual(['Boaty McBoatface'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_5(self):
        base = 'Boaty von Boatface, Nav.E. Massachusetts Institute of Technology'  # noqa
        self.assertEqual(['Boaty von Boatface'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_6(self):
        base = 'The Man, M.B.A. Massachusetts Institute of Technology'
        self.assertEqual(['The Man'], Person.clean_metadata(base))

    def test_clean_metadata_remove_degrees_7(self):
        base = 'Buzz Aldrin, Massachusetts Institute of Technology'
        self.assertEqual(['Buzz Aldrin'], Person.clean_metadata(base))

    def test_clean_metadata_multiple_people(self):
        base = 'Dr. Jekyll and Mr. Hyde'
        self.assertEqual(['Dr. Jekyll', 'Mr. Hyde'],
                         Person.clean_metadata(base))


class DepartmentTestCase(TestCase):
    fixtures = ['theses.json', 'departments.json', 'authors.json',
                'contributions.json']

    def test_clean_metadata_1(self):
        base = 'Massachusetts Institute of Technology. Department of Basketweaving'  # noqa
        self.assertEqual('Department of Basketweaving',
                         Department.clean_metadata(base))

    def test_clean_metadata_2(self):
        base = 'Dept. of Basketweaving'
        self.assertEqual('Department of Basketweaving',
                         Department.clean_metadata(base))

    def test_get_or_create_from_metadata(self):
        # A department is created.
        base = 'Department of Basketweaving'
        dept = Department.get_or_create_from_metadata(base)
        self.assertEqual(dept.name, 'Department of Basketweaving')

        # New departments are not created when we are fed metadata we already
        # know about - instead we fetch an existing one.
        base = 'Department of Basketweaving'
        dept2 = Department.get_or_create_from_metadata(base)
        self.assertEqual(dept.pk, dept2.pk)

        base = 'Dept. of Basketweaving'
        dept3 = Department.get_or_create_from_metadata(base)
        self.assertEqual(dept.pk, dept3.pk)


class ThesisTestCase(TestCase):
    fixtures = ['theses.json', 'departments.json', 'authors.json',
                'contributions.json']

    def test_add_single_new_person(self):
        name = 'Whitfield Diffie'
        thesis = Thesis.objects.first()

        assert not Person.objects.filter(name=name)

        thesis.add_people([name])
        # Don't use thesis.authors - since it's a cached property, it may not
        # have updated.
        author_names = [person.name for person in thesis.authors.all()]

        assert name in author_names

    def test_add_multiple_new_people(self):
        name1 = 'Limor Fried'
        name2 = 'Shirley Jackson'
        thesis = Thesis.objects.first()

        assert not Person.objects.filter(name=name1)
        assert not Person.objects.filter(name=name2)

        thesis.add_people([name1, name2])
        author_names = [person.name for person in thesis.authors.all()]

        assert name1 in author_names
        assert name2 in author_names

    def test_add_single_known_person(self):
        name = 'Irene Pepperberg'
        person = Person.objects.get_or_create(name=name)
        thesis = Thesis.objects.first()

        assert person not in thesis.authors

        thesis.add_people([name])
        author_names = [person.name for person in thesis.authors.all()]

        assert name in author_names

    def test_add_multiple_known_people(self):
        name1 = 'Oliver R. Smoot'
        name2 = 'Tom Magliozzi'
        name3 = 'Ray Magliozzi'
        thesis = Thesis.objects.first()

        oliver, _ = Person.objects.get_or_create(name=name1)
        tom, _ = Person.objects.get_or_create(name=name2)
        ray, _ = Person.objects.get_or_create(name=name3)

        assert oliver not in thesis.authors
        assert tom not in thesis.authors
        assert ray not in thesis.authors

        thesis.add_people([name1, name2, name3])

        assert oliver in thesis.authors.all()
        assert tom in thesis.authors.all()
        assert ray in thesis.authors.all()

    def test_add_an_advisor(self):
        name = 'Ellen Spertus'
        thesis = Thesis.objects.first()

        assert not Person.objects.filter(name=name)

        thesis.add_people([name], author=False)
        advisor_names = [person.name for person in thesis.advisors.all()]

        assert name in advisor_names

    def test_add_department(self):
        dept = 'Department of Baconology'
        thesis = Thesis.objects.first()
        thesis.add_departments([dept])

        dept_names = [dept.name for dept in thesis.department.all()]
        assert dept in dept_names

    def test_add_departments(self):
        dept1 = 'Department of Transwarp Technologies'
        dept2 = 'Department of Marshmallow Engineering'
        thesis = Thesis.objects.first()
        thesis.add_departments([dept1, dept2])

        dept_names = [dept.name for dept in thesis.department.all()]
        assert dept1 in dept_names
        assert dept2 in dept_names

    def test_add_known_department(self):
        name = 'Course Eleventy-One'
        dept, _ = Department.objects.get_or_create(name=name)
        thesis = Thesis.objects.first()

        assert dept not in thesis.department.all()

        thesis.add_departments([name])

        assert dept in thesis.department.all()

    def test_get_absolute_url(self):
        assert False
