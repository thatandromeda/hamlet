from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^similar_to/(?P<pk>\d+)/$',
        views.SimilarToView.as_view(), name='similar_to'),
    url(r'^similar_to/$',
        views.SimilarToSearchView.as_view(), name='similar_to'),
]
