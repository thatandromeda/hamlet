from django.urls import path

from . import views

app_name = 'citations'

urlpatterns = [
    path('lit_review_buddy/',
        views.LitReviewBuddyView.as_view(), name='lit_review_buddy'),
]
