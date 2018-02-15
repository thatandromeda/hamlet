from dal import autocomplete

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView

from .forms import (TitleAutocompleteForm,
                    AuthorAutocompleteForm,
                    UploadFileForm)
from .models import Thesis, Person, Contribution

from .document import factory


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
        identifier = self.kwargs.get('identifier', None)

        try:
            return Thesis.objects.get(identifier=identifier)
        except Thesis.DoesNotExist:
            raise Http404('No matching thesis was found')


class SimilarToByAuthorView(DetailView):
    """Given an author, shows the most similar theses to all of their works."""
    template_name = 'theses/similar_to_by_authors.html'
    model = Person

    def get_context_data(self, **kwargs):
        context = super(SimilarToByAuthorView, self).get_context_data(**kwargs)
        context['theses'] = []

        theses = self.get_theses()
        for thesis in theses:
            if thesis.unextractable:
                context['theses'].append({
                    'object': thesis,
                    'unextractable': True
                })
            else:
                context['theses'].append({
                    'object': thesis,
                    'suggestions': thesis.get_most_similar(topn=10)
                })

        return context

    def get_theses(self):
        contribs = Contribution.objects.filter(
            person=self.get_object(), role=Contribution.AUTHOR)

        return Thesis.objects.filter(contribution__in=contribs)


class SimilarToSearchView(TemplateView):
    """Enter a thesis or author so that the SimilarToViews can find it."""
    template_name = 'theses/search.html'

    def _handle_author(self, pk):
        try:
            author = Person.objects.get(pk=pk)
            url = reverse('theses:similar_to_by_author',
                          kwargs={'pk': author.pk})
            return HttpResponseRedirect(url)
        except Person.DoesNotExist:
            messages.error('No such author.')
            return HttpResponseRedirect('')

    def _handle_thesis(self, pk):
        thesis = Thesis.objects.get(pk=pk)
        url = reverse('theses:similar_to',
            kwargs={'identifier': thesis.identifier})
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super(SimilarToSearchView, self).get_context_data(**kwargs)
        context['title_form'] = TitleAutocompleteForm
        context['author_form'] = AuthorAutocompleteForm
        return context

    def post(self, request, *args, **kwargs):
        if 'author' in request.POST:
            return self._handle_author(request.POST['author'])
        elif 'title' in request.POST:
            return self._handle_thesis(request.POST['title'])
        else:
            messages.warning('Please submit an author or title.')
            return HttpResponseRedirect('')


class AutocompleteAuthorView(autocomplete.Select2QuerySetView):
    """enter a thesis so that the SimilarToView can find it"""
    def get_queryset(self):
        qs = Person.objects.filter(
            contribution__role=Contribution.AUTHOR).distinct()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class AutocompleteThesisView(autocomplete.Select2QuerySetView):
    """enter a thesis so that the SimilarToView can find it"""
    def get_queryset(self):
        qs = Thesis.objects.filter(unextractable=False).distinct()

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs


class UploadRecommendationView(FormView):
    template_name = 'theses/upload_recommend.html'
    form_class = UploadFileForm

    # Only return documents above this similarity threshold. (When similarity
    # gets too low, it becomes meaningless. "Too low" is an art, not a
    # science.)
    threshold = 0.65

    def _get_similar_documents(self, doc):
        vector = settings.NEURAL_NET.infer_vector(doc.words)

        # Find the most similar docvecs to this inferred vector.
        doclist = settings.NEURAL_NET.docvecs.most_similar([vector])

        # Limit to the documents above our similarity threshold. This gives a
        # list of document filenames.
        simdocs = [doc[0] for doc in doclist if doc[1] >= self.threshold]

        # Turn filenames into document identifiers so we can feed them to SQL.
        ids = [s.replace('1721.1-', '').replace('.txt', '') for s in simdocs]

        return Thesis.objects.filter(identifier__in=ids)

    def form_valid(self, form):
        context = {}
        doc = factory(self.request.FILES['file'])
        context['suggestions'] = self._get_similar_documents(doc)
        return render(self.request, 'theses/similar_to.html', context)
