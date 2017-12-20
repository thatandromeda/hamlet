from dal import autocomplete

from django.http import Http404
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from .forms import TitleAutocompleteForm, AuthorAutocompleteForm
from .models import Thesis, Person, Contribution


class SimilarToView(DetailView):
    """Given a Thesis, shows the most similar Theses."""
    template_name = 'theses/similar_to.html'

    def get_context_data(self, **kwargs):
        context = super(SimilarToView, self).get_context_data(**kwargs)

        thesis = self.get_object()
        if thesis.unextractable:
            context['unextractable'] = True
        else:
            context['suggestions'] = thesis.get_most_similar(topn=10)

        return context

    def get_object(self, queryset=None):
        identifier = self.kwargs.get(self.pk_url_kwarg, None)

        try:
            return Thesis.objects.get(identifier=identifier)
        except Thesis.DoesNotExist:
            raise Http404('No matching thesis was found')


class SimilarToSearchView(TemplateView):
    """enter a thesis so that the SimilarToView can find it"""
    template_name = 'theses/search.html'

    def get_context_data(self, **kwargs):
        context = super(SimilarToSearchView, self).get_context_data(**kwargs)
        context['title_form'] = TitleAutocompleteForm
        context['author_form'] = AuthorAutocompleteForm
        return context


class AutocompleteAuthorView(autocomplete.Select2QuerySetView):
    """enter a thesis so that the SimilarToView can find it"""
    def get_queryset(self):
        qs = Person.objects.filter(contribution__role=Contribution.AUTHOR)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class AutocompleteThesisView(autocomplete.Select2QuerySetView):
    """enter a thesis so that the SimilarToView can find it"""
    def get_queryset(self):
        qs = Thesis.objects.filter(unextractable=False)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs
