# An early version of the metadata cleaning function in
# hamlet.theses.models.Person truncated names too aggressively; this script
# refetches and reprocesses name data.

import os

from hamlet.theses.models import Thesis

from .train_neural_net import DocFetcher, MetadataWriter

DSPACE_OAI_IDENTIFIER = os.environ.get('DSPACE_OAI_IDENTIFIER')
DSPACE_OAI_URI = os.environ.get('DSPACE_OAI_URI')


def _get_datadict(fetcher, item):
    writer = MetadataWriter()
    metadata_mets = fetcher.get_record(DSPACE_OAI_URI,
        DSPACE_OAI_IDENTIFIER, item['identifier'], 'mets')
    metadata_dc = fetcher.get_record(DSPACE_OAI_URI,
        DSPACE_OAI_IDENTIFIER, item['identifier'], 'rdf')
    return writer.extract_metadata(metadata_dc, metadata_mets,
                        item['sets'])


def rewrite(max=0):
    count = 0
    fetcher = DocFetcher()

    items = fetcher.get_record_list(DSPACE_OAI_URI)
    parsed_items = fetcher.parse_record_list(items)

    for item in parsed_items:
        # First, setup: extract metadata; get thesis; make sure it doesn't
        # have authors yet.
        # If any of these metadata extraction steps fail, we'll skip adding
        # to the thesis. We can always check for theses with no authors later.
        try:
            # May throw exceptions due to failed metadata extraction.
            datadict = _get_datadict(fetcher, item)

            # Throw exception if datadict is empty.
            assert datadict

            # Throw exception if Thesis.DoesNotExist.
            thesis = Thesis.objects.get(identifier=datadict['id'])

            # Throw exception we've already found the thesis authors.
            assert not thesis.authors
        except:
            continue

        # Second, try to add authors to the thesis.
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
