from django.http import Http404
from django.views.generic import View
from django.views.generic.detail import DetailView

from .models import Thesis


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


class SimilarToSearchView(View):
    """enter a thesis so that the SimilarToView can find it"""
    pass
