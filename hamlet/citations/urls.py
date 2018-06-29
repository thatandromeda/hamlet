from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^lit_review_buddy/$',
        views.LitReviewBuddyView.as_view(), name='lit_review_buddy'),
]
