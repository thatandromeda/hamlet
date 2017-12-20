from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^similar_to/(?P<pk>\d+)/$',
        views.SimilarToView.as_view(), name='similar_to'),
    url(r'^similar_to/$',
        views.SimilarToSearchView.as_view(), name='similar_to'),
    url(r'^autocomplete/author/$',
        views.AutocompleteAuthorView.as_view(), name='autocomplete_author'),
    url(r'^autocomplete/thesis/$',
        views.AutocompleteThesisView.as_view(), name='autocomplete_thesis'),
]
