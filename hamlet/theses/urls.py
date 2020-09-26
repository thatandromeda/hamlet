from django.urls import path

from . import views

app_name = 'theses'

urlpatterns = [
    path('similar_to/',
        views.SimilarToSearchView.as_view(), name='similar_to'),
    path('similar_to/<int:identifier>/',
        views.SimilarToView.as_view(), name='similar_to'),
    path('similar_to/author/<int:pk>/',
        views.SimilarToByAuthorView.as_view(), name='similar_to_by_author'),
    path('autocomplete/author/',
        views.AutocompleteAuthorView.as_view(), name='autocomplete_author'),
    path('autocomplete/thesis/',
        views.AutocompleteThesisView.as_view(), name='autocomplete_thesis'),
    path('upload/recommend/',
        views.UploadRecommendationView.as_view(), name='upload_recommend'),
]
