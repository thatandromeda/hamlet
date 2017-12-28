import re

from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase, override_settings

from .forms import AuthorAutocompleteForm, TitleAutocompleteForm
from .models import Thesis, Person, Contribution
from . import views


# See http://tech.novapost.fr/django-unit-test-your-views-en.html .
def setup_view(view_class, request, *args, **kwargs):
    """Mimic as_view() returned callable, but returns view instance.

    args and kwargs are the same you would pass to ``reverse()``

    """
    view = view_class()
    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


@override_settings(COMPRESS_ENABLED=False)
class BaseTestCase(TestCase):
    fixtures = ['theses.json', 'departments.json', 'authors.json',
                'contributions.json']

    def setup(self):
        self.client = Client()


class SimilarToViewTests(BaseTestCase):

    def test_unextractable_not_shown(self):
        thesis = Thesis.objects.get(pk=32600)
        assert thesis.unextractable
        url = reverse('theses:similar_to',
            kwargs={'identifier': thesis.identifier})
        response = self.client.get(url)
        assert response.context['unextractable'] is True
        assert 'suggestions' not in response.context
        # There are no links to other theses.
        assert not re.search('/similar_to/\d+', str(response.content))

    def test_suggestion_context(self):
        thesis = Thesis.objects.get(pk=32174)
        assert not thesis.unextractable
        url = reverse('theses:similar_to',
            kwargs={'identifier': thesis.identifier})
        response = self.client.get(url)
        assert 'unextractable' not in response.context
        assert 'suggestions' in response.context

        pks = [t.pk for t in response.context['suggestions']]
        assert 39337 in pks
        assert 39391 in pks
        assert 41449 in pks
        assert 47003 in pks

        content = str(response.content)

        assert 'Energy and topology of heteropolymers' in content
        assert 'Neural mechanisms involved in memory formation and retrieval within the rodent hippocampus' in content  # noqa
        assert 'Essays on the emiprical properties of stock and mutual fund returns' in content  # noqa
        assert 'Quantification of benzo[a]pyrene-diol-epoxide adducts by laser-induced fluorescence spectroscopy' in content  # noqa

    def test_get_correct_object(self):
        # We use the thesis identifier in the URL to aid in URL hacking -
        # make sure we are getting the Thesis object by identifier and not by
        # pk.
        thesis = Thesis.objects.first()
        url = reverse('theses:similar_to',
            kwargs={'identifier': thesis.identifier})
        request = RequestFactory().get(url)
        view = setup_view(views.SimilarToView, request,
                          identifier=thesis.identifier)
        view_thesis = view.get_object()
        assert view_thesis.pk == thesis.pk


class SimilarToByAuthorViewTests(BaseTestCase):
    def test_correct_theses_in_context(self):
        url = reverse('theses:similar_to_by_author', kwargs={'pk': 29406})
        response = self.client.get(url)

        # Check assumption.
        assert response.context['theses'][0]['object'].pk == 32174

        pks = [t.pk for t in response.context['theses'][0]['suggestions']]
        assert 39337 in pks
        assert 39391 in pks
        assert 41449 in pks
        assert 47003 in pks

        content = str(response.content)

        assert 'Energy and topology of heteropolymers' in content
        assert 'Neural mechanisms involved in memory formation and retrieval within the rodent hippocampus' in content  # noqa
        assert 'Essays on the emiprical properties of stock and mutual fund returns' in content  # noqa
        assert 'Quantification of benzo[a]pyrene-diol-epoxide adducts by laser-induced fluorescence spectroscopy' in content  # noqa

    def test_get_theses(self):
        url = reverse('theses:similar_to_by_author', kwargs={'pk': 29406})
        request = RequestFactory().get(url)
        view = setup_view(views.SimilarToByAuthorView, request, pk=29406)
        view_theses = view.get_theses()

        pks = [t.pk for t in view_theses]
        assert [32174] == pks


class SimilarToSearchViewTests(BaseTestCase):
    def test_author_post_returns_author_view(self):
        response = self.client.post(reverse('theses:similar_to'),
            {'author': 29406})
        assert response.status_code == 302
        assert response.url == reverse('theses:similar_to_by_author',
            kwargs={'pk': 29406})

    def test_thesis_post_returns_thesis_view(self):
        response = self.client.post(reverse('theses:similar_to'),
            {'title': 32174})
        assert response.status_code == 302
        assert response.url == reverse('theses:similar_to',
            kwargs={'identifier': Thesis.objects.get(pk=32174).identifier})

    def test_author_form_in_context(self):
        response = self.client.get(reverse('theses:similar_to'))
        assert 'author_form' in response.context
        # Note the parentheses - we're checking the class of the form *as
        # instantiated*. The object passed into the context is actually the
        # uninstantiated form class, so it is actually an instance of the
        # metaclass, which is unhelpful.
        assert isinstance(response.context['author_form'](),
            AuthorAutocompleteForm)

    def test_thesis_form_in_context(self):
        response = self.client.get(reverse('theses:similar_to'))
        assert 'title_form' in response.context
        assert isinstance(response.context['title_form'](),
            TitleAutocompleteForm)


class AutocompleteAuthorViewTests(BaseTestCase):
    def test_base_queryset_is_all_authors(self):
        url = reverse('theses:autocomplete_author')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteAuthorView, request)
        view.q = None

        db_authors = Person.objects.filter(
            contribution__role=Contribution.AUTHOR).distinct()
        view_authors = view.get_queryset()
        assert (set([a.pk for a in view_authors]) ==
                set([a.pk for a in db_authors]))

    def test_base_queryset_is_distinct(self):
        url = reverse('theses:autocomplete_author')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteAuthorView, request)
        view.q = None

        db_authors = Person.objects.filter(
            contribution__role=Contribution.AUTHOR).distinct()
        view_authors = view.get_queryset()
        assert len(view_authors) == len(db_authors)

    def test_filtered_queryset(self):
        url = reverse('theses:autocomplete_author')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteAuthorView, request)
        view.q = 'Witonsky'

        view_authors = view.get_queryset()
        db_authors = Person.objects.filter(
            contribution__role=Contribution.AUTHOR,
            name__icontains='Witonsky').distinct()

        assert len(view_authors) == len(db_authors)
        assert (set([a.pk for a in view_authors]) ==
                set([a.pk for a in db_authors]))

    def test_filtered_queryset_empty(self):
        url = reverse('theses:autocomplete_author')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteAuthorView, request)
        view.q = 'Outis'

        view_authors = view.get_queryset()
        db_authors = Person.objects.filter(
            contribution__role=Contribution.AUTHOR,
            name__icontains='Outis').distinct()
        assert not db_authors
        assert not view_authors


class AutocompleteThesisViewTests(BaseTestCase):
    def test_base_queryset_is_all_extractable_theses(self):
        url = reverse('theses:autocomplete_thesis')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteThesisView, request)
        view.q = None

        db_theses = Thesis.objects.filter(unextractable=False).distinct()
        view_theses = view.get_queryset()
        assert (set([a.pk for a in view_theses]) ==
                set([a.pk for a in db_theses]))

    def test_base_queryset_is_distinct(self):
        url = reverse('theses:autocomplete_thesis')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteThesisView, request)
        view.q = None

        db_theses = Thesis.objects.filter(unextractable=False).distinct()
        view_theses = view.get_queryset()
        assert len(view_theses) == len(db_theses)

    def test_filtered_queryset(self):
        url = reverse('theses:autocomplete_thesis')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteThesisView, request)
        view.q = 'IntraCavity'

        db_theses = Thesis.objects.filter(
            unextractable=False,
            title__icontains='IntraCavity').distinct()
        view_theses = view.get_queryset()
        assert (set([a.pk for a in view_theses]) ==
                set([a.pk for a in db_theses]))
        assert len(view_theses) == len(db_theses)

    def test_filtered_queryset_empty(self):
        query = 'Emoji-based catalysis of strongly typed photon genotypes'
        url = reverse('theses:autocomplete_thesis')
        request = RequestFactory().get(url)
        view = setup_view(views.AutocompleteThesisView, request)
        view.q = query

        db_theses = Thesis.objects.filter(
            unextractable=False,
            title__icontains=query).distinct()
        view_theses = view.get_queryset()
        assert not view_theses
        assert not db_theses
