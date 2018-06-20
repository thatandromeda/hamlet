# An early version of the metadata cleaning function in
# hamlet.theses.models.Person truncated names too aggressively; this script
# refetches and reprocesses name data.

import os

from hamlet.theses.models import Thesis

from .train_neural_net import DocFetcher, MetadataWriter

DSPACE_OAI_IDENTIFIER = os.environ.get('DSPACE_OAI_IDENTIFIER')
DSPACE_OAI_URI = os.environ.get('DSPACE_OAI_URI')


def rewrite(max=0):
    count = 0
    fetcher = DocFetcher()
    writer = MetadataWriter()

    items = fetcher.get_record_list(DSPACE_OAI_URI)
    parsed_items = fetcher.parse_record_list(items)

    for item in parsed_items:
        # If any of these metadata extraction steps fail, we'll skip adding
        # to the thesis. We can always check for theses with no authors later.
        try:
            metadata_mets = fetcher.get_record(DSPACE_OAI_URI,
                DSPACE_OAI_IDENTIFIER, item['identifier'], 'mets')
            metadata_dc = fetcher.get_record(DSPACE_OAI_URI,
                DSPACE_OAI_IDENTIFIER, item['identifier'], 'rdf')
            datadict = writer.extract_metadata(metadata_dc, metadata_mets,
                                item['sets'])
        except:
            continue

        if not datadict:
            continue

        try:
            thesis = Thesis.objects.get(identifier=datadict['id'])
        except Thesis.DoesNotExist:
            continue

        if thesis.authors:
            continue

        try:
            thesis.add_people(datadict['authors'])
            thesis.add_people(datadict['advisors'], author=False)
            print('Updated {}'.format(thesis.id))
            count += 1
        except:
            # We'll have to deal with these manually.
            print("Could not add authors to thesis with pk {}".format(thesis.id))

        if max and (count > max):
            break
