from django.shortcuts import render
from django.views.generic.edit import FormView

from hamlet.common.document import factory
from hamlet.common.forms import UploadFileForm
from hamlet.common.inferred_vectors import get_similar_documents


class LitReviewBuddyView(FormView):
    template_name = 'citations/lit_review_buddy.html'
    form_class = UploadFileForm

    def form_valid(self, form):
        context = {}
        doc = factory(self.request.FILES['file'])
        simdocs = get_similar_documents(doc)
        context['suggestions'] = simdocs
        context['total_suggestions'] = sum([
            doc.citation_set.count() for doc in simdocs
        ])
        return render(self.request, 'citations/lit_review_outcomes.html',
            context)
