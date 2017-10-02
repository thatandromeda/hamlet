import argparse
import json
import logging
import os
from string import punctuation
import time
import xml.etree.ElementTree as ET

from gensim.models.doc2vec import LabeledSentence, Doc2Vec
from nltk import sent_tokenize, WordPunctTokenizer
import requests
from tika import parser as tikaparser

from local_settings import DSPACE_OAI_IDENTIFIER, DSPACE_OAI_URI

# Get documents
# Thoughts...
# It's 843G of docs. I only have 402 on my machine. So I need to plan on
# starting with a subset - which I should *anyway* - but I also need to think
# about what's resident in memory when.
# Do I need to load the entire corpus into memory to do training or is a
# stepwise thing happening?
# For step 1, I should just get a single-department subdirectory and scp it
# over to my machine. The goal here is to make sure the code runs at all,
# address tokenization, etc.
# Next step will involve network file access.

# See https://medium.com/@klintcho/doc2vec-tutorial-using-gensim-ab3ac03d3a1

logger = logging.getLogger(__name__)

THESIS_SUBDIRS = [
    'aero_astro',
    'architecture',
    'biological_engineering',
    'biology',
    'brain_and_cognitive',
    'chemical_engineering',
    'chemistry',
    'civil_and_environmental_engineering',
    'comp_media_studies',
    'computational_and_systems_biology',
    'computation_for_design_and_optimization',
    'earth_atmo_planetary_sciences',
    'economics',
    'eecs',
    'engineering_systems_division',
    'harvard_mit_health_sciences_and_technology',
    'humanities',
    'institute_data_systems_society',
    'linguistics_and_philosophy',
    'materials_science_and_engineering',
    'mathematics',
    'mechanical_engineering',
    'media_arts_and_sciences',
    'nuclear_engineering',
    'ocean_engineering',
    'operations_research_center',
    'physics',
    'political_science',
    'program_in_real_estate_development',
    'program_writing_humanistic_studies',
    'science_technology_society',
    'sloan_school',
    'systems_design_and_management',
    'technology_and_policy_program',
    'urban_studies_and_planning',
    'various_historical_departments'
]

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CUR_DIR + '/thesis_set_list.json', 'r') as f:
    THESIS_SET_LIST = json.loads(f.read())


class LabeledLineSentence(object):
    def __init__(self, doc_yielder):
        self.doc_yielder = doc_yielder

    def __iter__(self):
        for handle, doc in self.doc_yielder:
            yield LabeledSentence(words=self._tokenize(doc), tags=[handle])

    def _tokenize(self, doc):
        all_tokens = []
        sentences = sent_tokenize(doc)

        tokenizer = WordPunctTokenizer()
        for sentence in sentences:
            words = tokenizer.tokenize(sentence.lower())
            words = [word for word in words if word not in punctuation]
            all_tokens.extend(words)
        return all_tokens


class DocYielder(object):
    METS_NAMESPACE = {'mets': 'http://www.loc.gov/METS/',
                      'mods': 'http://www.loc.gov/mods/v3',
                      'oai': 'http://www.openarchives.org/OAI/2.0/'}
    DOCS_CACHE = {}

    def get_record(self, dspace_oai_uri, dspace_oai_identifier, identifier,
                   metadata_format):
        '''Gets metadata record for a single item in OAI-PMH repository in
        specified metadata format.
        '''
        params = {'verb': 'GetRecord',
                  'identifier': dspace_oai_identifier + identifier,
                  'metadataPrefix': metadata_format}
        r = requests.get(dspace_oai_uri, params=params)
        return r.text

    def get_record_list(self, dspace_oai_uri, metadata_format, start_date=None,
                        end_date=None):
        '''Returns a list of record headers for items in OAI-PMH repository.
        Must pass in desired metadata format prefix. Can optionally pass
        bounding dates to limit harvest.
        '''
        params = {'verb': 'ListIdentifiers', 'metadataPrefix': metadata_format}

        if start_date:
            params['from'] = start_date
        if end_date:
            params['until'] = end_date

        r = requests.get(dspace_oai_uri, params=params)
        return r.text

    def parse_record_list(self, record_xml):
        xml = ET.fromstring(record_xml)
        records = xml.findall('.//oai:header', self.METS_NAMESPACE)
        for record in records:
            handle = record.find('oai:identifier', self.METS_NAMESPACE).text\
                .replace('oai:dspace.mit.edu:', '').replace('/', '-')
            identifier = handle.replace('1721.1-', '')
            setSpecs = record.findall('oai:setSpec', self.METS_NAMESPACE)
            sets = [s.text for s in setSpecs]
            yield {'handle': handle, 'identifier': identifier, 'sets': sets}

    def is_thesis(self, item):
        '''Returns True if any set_spec in given sets is in the
        thesis_set_spec_list, otherwise returns false.
        '''
        try:
            return self.DOCS_CACHE[item['handle']]['is_thesis']
        except KeyError:
            ans = any((s in THESIS_SET_LIST.keys() for s in item['sets']))
            self.DOCS_CACHE[item['handle']]['is_thesis'] = ans
            return ans

    def get_pdf_url(self, mets):
        '''Gets and returns download URL for PDF from METS record.
        '''
        record = mets.find('.//mets:file[@MIMETYPE="application/pdf"]/',
                           self.METS_NAMESPACE)

        url = record.get('{http://www.w3.org/1999/xlink}href')
        if url:
            url = url.replace('http://', 'https://')

        return url

    def get_single_network_file(self, item, metadata_format):
        metadata = self.get_record(DSPACE_OAI_URI, DSPACE_OAI_IDENTIFIER,
                              item['identifier'], metadata_format)
        mets = ET.fromstring(metadata)
        pdf_url = self.get_pdf_url(mets)

        if not pdf_url:
            return

        with open(item['handle'], 'wb') as f:
            r = requests.get(pdf_url, stream=True)
            r.raise_for_status()
            for chunk in r.iter_content(1024):
                f.write(chunk)
            f.flush()
            self.DOCS_CACHE[item['handle']]['filename'] = f.name

    def extract_text(self, item):
        if 'textfile' in self.DOCS_CACHE[item['handle']].keys():
            with open(self.DOCS_CACHE[item['handle']]['textfile'], 'r') as f:
                return f.read()

        fn = CUR_DIR + '/files/' + self.DOCS_CACHE[item['handle']]['filename']
        parsed = tikaparser.from_file(fn)
        content = parsed['content']
        textfile = fn + '.txt'
        with open(textfile, 'w') as f:
            f.write(content)

        self.DOCS_CACHE[item['handle']]['textfile'] = textfile

        return content

    # TODO:
    # Write files locally so that you don't have to fetch and extract them
    # each time you do a training epoch. Check for their existence before
    # grabbing them.
    # but put an upper bound on the amount of space you're willing to fill with
    # network files.
    # Also cache the results of not_a_thesis.
    def __iter__(self, metadata_format='mets', start_date=None,
                 end_date=None):
        items = self.get_record_list(DSPACE_OAI_URI, metadata_format,
                                     start_date, end_date)
        parsed_items = self.parse_record_list(items)

        total_items_processed = 0

        for item in parsed_items:
            if item['handle'] not in self.DOCS_CACHE.keys():
                self.DOCS_CACHE[item['handle']] = {}

            total_items_processed += 1
            if not self.is_thesis(item):
                continue

            print('Processing item %s' % item['handle'])
            if 'filename' not in self.DOCS_CACHE[item['handle']].keys():
                self.get_single_network_file(item, metadata_format)

            try:
                yield (item['handle'], self.extract_text(item))
            except:
                print('That failed')
                continue

            if total_items_processed >= 10:
                break


class ModelTrainer(object):
    def execute(self, args):
        self.train_model(args.filename)

    def get_iterator(self):
        doc_yielder = DocYielder()
        return LabeledLineSentence(doc_yielder)

    def train_model(self, filename):
        model = Doc2Vec(alpha=0.025,
                        min_alpha=0.025)

        doc_iterator = self.get_iterator()
        print("Building vocab for %s..." % filename)
        model.build_vocab(doc_iterator)

        for epoch in range(10):
            start_time = time.time()
            print("=== Training epoch {} ===".format(epoch))
            model.train(doc_iterator,
                        total_examples=model.corpus_count,
                        epochs=model.iter)
            print("Finished training, took {}".format(
                time.time() - start_time))

        model.save('{filename}.model'.format(filename=filename))
        return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train a neural net on .txt '
        'files located in the documents/ directory.')
    parser.add_argument('filename', help="Base filename of saved model")

    args = parser.parse_args()
    ModelTrainer().execute(args)
