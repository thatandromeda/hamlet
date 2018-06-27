from django.conf import settings

from hamlet.theses.models import Thesis


def get_similar_documents(doc):
    # Only return documents above this similarity threshold. (When similarity
    # gets too low, it becomes meaningless. "Too low" is an art, not a
    # science.)
    threshold = 0.65

    vector = settings.NEURAL_NET.infer_vector(doc.words)

    # Find the most similar docvecs to this inferred vector.
    doclist = settings.NEURAL_NET.docvecs.most_similar([vector])

    # Limit to the documents above our similarity threshold. This gives a
    # list of document filenames.
    simdocs = [doc[0] for doc in doclist if doc[1] >= threshold]

    # Turn filenames into document identifiers so we can feed them to SQL.
    ids = [s.replace('1721.1-', '').replace('.txt', '') for s in simdocs]

    return Thesis.objects.filter(identifier__in=ids)
