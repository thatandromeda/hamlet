import re

from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase, override_settings

from .models import Thesis
from . import views


# See http://tech.novapost.fr/django-unit-test-your-views-en.html .
def setup_view(view, request, *args, **kwargs):
    """Mimic as_view() returned callable, but returns view instance.

    args and kwargs are the same you would pass to ``reverse()``

    """
    view.request = request
    view.args = args
    view.kwargs = kwargs
    return view


@override_settings(COMPRESS_ENABLED=False)
class BaseTestCase(TestCase):
    fixtures = ['theses.json', 'departments.json']

    def setup(self):
        self.client = Client()


class SimilarToViewTests(BaseTestCase):

    def test_unextractable_not_shown(self):
        thesis = Thesis.objects.filter(unextractable=True).first()
        url = reverse('theses:similar_to',
            kwargs={'identifier': thesis.identifier})
        response = self.client.get(url)
        assert response.context['unextractable'] is True
        assert 'suggestions' not in response.context
        # There are no links to other theses.
        assert not re.search('/similar_to/\d+', str(response.content))

    def test_suggestion_context(self):
        thesis = Thesis.objects.filter(unextractable=False).first()
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
        view_thesis = view.get_object(view)
        assert view_thesis.pk == thesis.pk


class SimilarToByAuthorViewTests(BaseTestCase):
    def test_correct_theses_in_context(self):
        assert False

    def test_unextractable_correctly_marked(self):
        assert False


class SimilarToSearchViewTests(BaseTestCase):
    def test_author_post_returns_author_view(self):
        assert False

    def test_thesis_post_returns_thesis_view(self):
        assert False

    def test_author_form_in_context(self):
        assert False

    def test_thesis_form_in_context(self):
        assert False


class AutocompleteAuthorViewTests(BaseTestCase):
    def test_base_queryset_is_all_authors(self):
        assert False

    def test_base_queryset_is_distinct(self):
        assert False

    def test_filtered_queryset(self):
        assert False


class AutocompleteThesisViewTests(BaseTestCase):
    def test_base_queryset_is_all_extractable_theses(self):
        assert False

    def test_base_queryset_is_distinct(self):
        assert False

    def test_filtered_queryset(self):
        assert False
