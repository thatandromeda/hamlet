from django.views.generic import TemplateView


class LitReviewBuddyView(TemplateView):
    template_name = 'citations/lit_review_buddy.html'
