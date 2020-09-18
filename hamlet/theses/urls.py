from django.conf.urls import url

from . import views

app_name = 'theses'

urlpatterns = [
    url(r'^similar_to/$',
        views.SimilarToSearchView.as_view(), name='similar_to'),
    url(r'^similar_to/(?P<identifier>\d+)/$',
        views.SimilarToView.as_view(), name='similar_to'),
    url(r'^similar_to/author/(?P<pk>\d+)/$',
        views.SimilarToByAuthorView.as_view(), name='similar_to_by_author'),
    url(r'^autocomplete/author/$',
        views.AutocompleteAuthorView.as_view(), name='autocomplete_author'),
    url(r'^autocomplete/thesis/$',
        views.AutocompleteThesisView.as_view(), name='autocomplete_thesis'),
    url(r'^upload/recommend/$',
        views.UploadRecommendationView.as_view(), name='upload_recommend'),
]
