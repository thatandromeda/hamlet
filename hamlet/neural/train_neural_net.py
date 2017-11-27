from glob import glob
import json
import logging
import os
import random
import re
import shutil
from string import punctuation
import time
import xml.etree.ElementTree as ET

from gensim.models.doc2vec import LabeledSentence, Doc2Vec
from nltk import sent_tokenize, WordPunctTokenizer
import requests
from tika import parser as tikaparser

from django.db.models import Count
from django.db.utils import DataError

from hamlet.theses.models import Thesis, Contribution, Person

# See https://medium.com/@klintcho/doc2vec-tutorial-using-gensim-ab3ac03d3a1

logger = logging.getLogger(__name__)

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CUR_DIR + '/thesis_set_list.json', 'r') as f:
    THESIS_SET_LIST = json.loads(f.read())

DSPACE_OAI_IDENTIFIER = os.environ.get('DSPACE_OAI_IDENTIFIER')
DSPACE_OAI_URI = os.environ.get('DSPACE_OAI_URI')

# Where to put the files we train on.
FILES_DIR = 'files'

METS_NAMESPACE = {'mets': 'http://www.loc.gov/METS/',
                  'mods': 'http://www.loc.gov/mods/v3',
                  'oai': 'http://www.openarchives.org/OAI/2.0/',
                  'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                  'dc': 'http://purl.org/dc/elements/1.1/',
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}


class LabeledLineSentence(object):
    def __init__(self, subdir):
        doc_list = glob(os.path.join(CUR_DIR, FILES_DIR, subdir, '*'))

        self.doc_list = [doc for doc in doc_list if doc.endswith('.txt')]

    def __iter__(self):
        for filename in self.doc_list:
            with open(filename, 'r') as f:
                doc = f.read()
            yield LabeledSentence(words=self._tokenize(doc),
                                  tags=[os.path.basename(filename)])

    def _tokenize(self, doc):
        all_tokens = []
        sentences = sent_tokenize(doc)

        tokenizer = WordPunctTokenizer()
        for sentence in sentences:
            words = tokenizer.tokenize(sentence.lower())
            words = [word for word in words if word not in punctuation]
            all_tokens.extend(words)
        return all_tokens


class MetadataWriter(object):
    DEGREE_OPTIONS = ["Bachelor's degree",
                      "Engineer's degree",
                      "Master's degree",
                      "Ph.D. / Sc.D."]

    def extract_contributors(self, metadata):
        # Includes advisor and department.
        contributors = metadata.findall('.//dc:contributor', METS_NAMESPACE)
        advisors = []
        departments = []

        for contributor in contributors:
            text = contributor.text
            if not text:
                continue
            if any(['Massachusetts Institute' in text,
                    'Dept' in text,
                    'Department' in text]):
                departments.append(text)
            else:
                advisors.append(text)
        return advisors, departments

    def extract_date(self, metadata):
        # There will be several (representing copyright, accessioning, etc.)
        # The copyright date will be a four-digit year. Find the earliest
        # year (there may be a substantial difference between copyright year
        # and archival processing years).
        date_format = r'^[0-9]{4}$'
        dates = metadata.findall('.//dc:date', METS_NAMESPACE)
        earliest = 20000
        for date in dates:
            if re.match(date_format, date.text):
                year = int(date.text)
                if year < earliest:
                    earliest = year
        return earliest

    def extract_degree_from_sets(self, item_sets):
        """Get degree from thesis set name if possible.

        This is easier than parsing the metadata but doesn't always work, so we
        try it first and fall back to metadata parsing if needed."""
        for item_set in item_sets:
            try:
                candidate = THESIS_SET_LIST[item_set].split('-')[1].strip()
                if candidate in self.DEGREE_OPTIONS:
                    return candidate
            except (IndexError, KeyError):
                # If the set text isn't of the form "Department - Degree",
                # taking an element from the split() will fail. That's ok.
                continue

        return None

    def extract_degree(self, metadata, item_sets):
        if item_sets:
            degree = self.extract_degree_from_sets(item_sets)
            if degree:
                return degree

        try:
            result = [e.text for e in
                      self.mets.findall('.//mods:note', METS_NAMESPACE) if
                      e.text is not None and
                      (e.text.startswith('Thesis') or
                       e.text.startswith('Massachusetts Institute of '
                                         'Technology'))]
        except AttributeError:
            result = None
        deg_text = result[0] if result else None

        return Thesis.extract_degree(deg_text) if deg_text else None

    def extract_identifier(self, metadata):
        identifiers = metadata.findall('.//dc:identifier', METS_NAMESPACE)
        id_str = None
        matcher = r'http[s]?://hdl.handle.net/1721.1/([0-9]*)'

        # There may be multiple identifiers; find the first that looks like a
        # handle.
        for identifier in identifiers:
            try:
                id_str = re.match(matcher, identifier.text).groups()[0]
                return int(id_str)
            except AttributeError:
                continue

    def extract_metadata(self, metadata_dc, metadata_mets, item_sets):
        try:
            dc = ET.fromstring(metadata_dc)
            mets = ET.fromstring(metadata_mets)
        except ET.ParseError:
            return None

        authors = dc.findall('.//dc:creator', METS_NAMESPACE)
        advisors, departments = self.extract_contributors(dc)
        date = self.extract_date(dc)
        degree = self.extract_degree(mets, item_sets)
        id = self.extract_identifier(dc)
        title = self.extract_title(mets)
        url = self.extract_url(mets)

        return {'authors': [author.text for author in authors],
                'advisors': advisors,
                'date': date,
                'degree': degree,
                'departments': departments,
                'id': id,
                'title': title,
                'url': url}

    def extract_title(self, mets):
        title = mets.find('.//mods:title', METS_NAMESPACE)
        try:
            return title.text
        except:
            return ''

    def extract_url(self, mets):
        record = mets.find('.//mets:file[@MIMETYPE="application/pdf"]/',
                           METS_NAMESPACE)

        # Do this instead of "if not record: return", because record will be
        # falsy *even when it exists*.
        try:
            url = record.get('{http://www.w3.org/1999/xlink}href')
        except:
            return None

        if url:
            url = url.replace('http://', 'https://')

        return url

    def write(self, metadata_dc, metadata_mets, item_sets):
        datadict = self.extract_metadata(metadata_dc, metadata_mets, item_sets)
        if not datadict:
            return False
        # Catch non-thesis objects.
        required = ['title', 'url', 'date', 'id', 'degree', 'authors',
                    'advisors', 'departments']
        if not all([datadict[key] for key in required]):
            return False

        try:
            Thesis.objects.get(identifier=datadict['id'])
        except Thesis.DoesNotExist:
            try:
                thesis = Thesis.objects.create(
                    title=datadict['title'],
                    url=datadict['url'],
                    year=datadict['date'],
                    identifier=datadict['id'],
                    degree=datadict['degree']
                )
                print('Created {}'.format(thesis.id))
                thesis.add_people(datadict['authors'])
                thesis.add_people(datadict['advisors'], author=False)
                thesis.add_departments(datadict['departments'])
            except DataError as e:
                print('~~~~~~Failed; identifier was {}'.format(datadict['id']))
                print(e)

        return True


class DocFetcher(object):
    DOCS_CACHE = {}
    WRITER = MetadataWriter()

    def get_network_files(self, args, start_date=None, end_date=None):
        print('Network files!!!!!!')
        items = self.get_record_list(DSPACE_OAI_URI, start_date, end_date)
        parsed_items = self.parse_record_list(items)
        total_items_processed = 0

        for item in parsed_items:
            if item['handle'] not in self.DOCS_CACHE.keys():
                self.DOCS_CACHE[item['handle']] = {}

            if not self.is_thesis(item):
                continue
            print('Processing {}'.format(item['handle']))

            total_items_processed += 1

            print('Processing item %s' % item['handle'])
            if 'textfile' not in self.DOCS_CACHE[item['handle']].keys():
                self.get_single_network_file(item, args)

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

    def get_record_list(self, dspace_oai_uri, start_date=None,
                        end_date=None):
        '''Returns a list of record headers for items in OAI-PMH repository.
        Must pass in desired metadata format prefix. Can optionally pass
        bounding dates to limit harvest.
        '''
        params = {'verb': 'ListIdentifiers', 'metadataPrefix': 'mets'}

        if start_date:
            params['from'] = start_date
        if end_date:
            params['until'] = end_date

        r = requests.get(dspace_oai_uri, params=params)
        return r.text

    def get_single_network_file(self, item, args):
        if Thesis.objects.filter(identifier=item['identifier']):
            return

        metadata_mets = self.get_record(DSPACE_OAI_URI, DSPACE_OAI_IDENTIFIER,
                                        item['identifier'], 'mets')

        # The available formats are oai_dc; qdc; rdf; ore; and mets. None of
        # them match the Dublin Core displayed at dspace.mit.edu, but rdf seems
        # to have the content we want. To get a list of all verbs, issue a
        # get request to the OAI endpoint with
        # params={'verb': 'ListMetadataFormats'}.
        metadata_dc = self.get_record(DSPACE_OAI_URI, DSPACE_OAI_IDENTIFIER,
                                      item['identifier'], 'rdf')

        if args['write_metadata']:
            outcome = self.write_metadata(metadata_dc,
                                          metadata_mets,
                                          item['sets'])
            if not outcome:
                return

    def is_thesis(self, item):
        '''Returns True if any set_spec in given sets is in the
        thesis_set_spec_list, otherwise returns false.
        '''
        # There are some things that are in the Thesis set but aren't really
        # theses (e.g. they are technical reports). These things will fail when
        # we try to extract their departments or degrees; we should filter them
        # out at that point.
        try:
            return self.DOCS_CACHE[item['handle']]['is_thesis']
        except KeyError:
            ans = any([s in THESIS_SET_LIST.keys()for s in item['sets']])
            self.DOCS_CACHE[item['handle']]['is_thesis'] = ans
            return ans

    def parse_record_list(self, record_xml):
        xml = ET.fromstring(record_xml)
        records = xml.findall('.//oai:header', METS_NAMESPACE)
        for record in records:
            handle = record.find('oai:identifier', METS_NAMESPACE).text\
                .replace('oai:dspace.mit.edu:', '').replace('/', '-')
            identifier = handle.replace('1721.1-', '')
            setSpecs = record.findall('oai:setSpec', METS_NAMESPACE)
            sets = [s.text for s in setSpecs]
            yield {'handle': handle, 'identifier': identifier, 'sets': sets}

    def write_metadata(self, metadata_dc, metadata_mets, item_sets):
        return self.WRITER.write(metadata_dc, metadata_mets, item_sets)


class ModelTrainer(object):
    # Accept queryset of Theses as arg
    # Fetch network data
    #   Check if it's in a main directory already; if so, ignore
    #   otherwise, fetch file, extract text, and write to main directory
    # Split test and training sets
    #   For all files in our set, cp from main to test or training
    # Train test model
    # Train training model
    MAIN_FILES_DIR = os.path.join(CUR_DIR, FILES_DIR, 'main')
    STARTING_FILES = os.listdir(MAIN_FILES_DIR)

    def __init__(self, files_subdirs=None):
        # If a list of subdirectory names is passed in, ModelTrainer will
        # split files into those directories and train a model on each.
        # If not, it will train on the entire contents of the main file
        # directory.
        if not files_subdirs:
            files_subdirs = ['main']

        self.FILES_SUBDIRS = files_subdirs

    def reset_directories(self):
        print('Resetting directories')
        training_dir = os.path.join(CUR_DIR, FILES_DIR, 'training')
        test_dir = os.path.join(CUR_DIR, FILES_DIR, 'test')
        shutil.rmtree(training_dir)
        shutil.rmtree(test_dir)
        os.mkdir(training_dir)
        os.mkdir(test_dir)

    def get_filename(self, thesis):
        return '1721.1-{}.txt'.format(thesis.identifier)

    def fetch_and_write_file(self, thesis, pdf_filepath):
        print('Fetching network file for thesis {}'.format(thesis.identifier))
        with open(pdf_filepath, 'wb') as f:
            r = requests.get(thesis.url, stream=True)
            r.raise_for_status()
            for chunk in r.iter_content(1024):
                f.write(chunk)
            f.flush()

    def extract_text(self, thesis):
        # If we've already extracted this file, let's not do it again.
        filename = self.get_filename(thesis)
        if filename in self.STARTING_FILES:
            print('File already gotten; continuing')
            return

        pdf_filepath = os.path.join(self.MAIN_FILES_DIR, 'temp.pdf')
        filepath = os.path.join(self.MAIN_FILES_DIR, filename)
        try:
            self.fetch_and_write_file(thesis, pdf_filepath)
        except:
            print('~~~~~~WARNING: Download failed for {}'.format(thesis.identifier))
            return

        print('Extracting pdf text from {}'.format(thesis.identifier))
        try:
            parsed = tikaparser.from_file(pdf_filepath)
        except:
            thesis.unextractable = True
            thesis.save()
            return

        try:
            content = parsed['content']
        except KeyError:
            thesis.unextractable = True
            thesis.save()
            return

        if not content:
            thesis.unextractable = True
            thesis.save()
            return
        with open(filepath, 'w') as f:
            f.write(content)

        os.remove(pdf_filepath)

    def split_data(self, queryset):
        """
        Randomly assigns to training or test set, by copying the file to the
        test or training directory. Weighted, such that 80% of objects end up
        in the training set.
        """
        # Clear test/training directories.
        self.reset_directories()

        print('Splitting test and training sets')
        # Sort theses into test/training directories. Throw out some of them
        # to save on memory usage during training and file size after -
        # we'll use the test set metric to gauge whether the trained model
        # generalizes.
        for thesis in queryset:
            set_dir = random.choices(self.FILES_SUBDIRS + [None],
                                     weights=[3, 1, 6])[0]
            if not set_dir:
                continue
            filename = self.get_filename(thesis)
            filepath = os.path.join(self.MAIN_FILES_DIR, filename)
            destination = os.path.join(CUR_DIR, FILES_DIR, set_dir)
            shutil.copy2(filepath, destination)

    def get_iterator(self, subdir):
        return LabeledLineSentence(subdir)

    def inner_train_model(self, window, size, iterator, filename):
        model = Doc2Vec(alpha=0.025,
                        # Alpha starts at `alpha` and decreases to
                        # `min_alpha`
                        min_alpha=0.025,
                        # Size of DBOW window (default=5).
                        window=window,
                        # Feature vector dimensionality (default=100).
                        size=size,
                        # Min word frequency for inclusion (default=5).
                        min_count=10)

        print("Building vocab for %s..." % filename)
        model.build_vocab(iterator)

        print("Training %s..." % filename)
        model.train(iterator,
                    total_examples=model.corpus_count,
                    epochs=model.iter)

        fn = '{}_w{}_s{}.model'.format(filename, window, size)
        filepath = os.path.join(CUR_DIR, 'nets', fn)
        model.save(filepath)

    def train_model(self, filename, queryset=Thesis.objects.all()):
        # Don't bother with theses when we know we can't get text from them.
        queryset = queryset.filter(unextractable=False)
        print('About to extract all text')
        for thesis in queryset:
            self.extract_text(thesis)

        print('All text extracted; time to get our ML on')

        iterators = []
        if self.FILES_SUBDIRS:
            self.split_data(queryset)
            for subdir in self.FILES_SUBDIRS:
                iterators.append(self.get_iterator(subdir))
        else:
                iterators.append(self.get_iterator(None))

        for window in range(3, 10):
            for step in range(1, 5):
                size = step * 52  # Multiples of 4 have better performance.
                start_time = time.time()

                print('Training with parameters window={}, '
                      'size={}'.format(window, size))
                for iterator in iterators:
                    self.inner_train_model(window, size,
                                           iterator,
                                           '{}_train'.format(filename))

                print('Finished training, took {}'.format(
                    time.time() - start_time))


class Evaluator(object):
    """
    The Evaluator assumes that, if we have two theses A and B which we expect
    to be similar, and another C which we expect to be unlike A and B, a
    good model will place A and B much closer together than A and C or B and C.

    It:
    * takes a list of models and a queryset they were trained on
    * selects tuples (A, B, C) of suitable theses within the queryset
    * sums sim(A, B) - sim(A, C) and sim(A, B) - sim(B, C) for all tuples for
      the given model
    * uses that sum as a score
    * ranks the models according to that score (highest is best)

    To choose tuples:
    * A, B are chosen such that they share an advisor, and thus we assume they
      are on similar topics
    * C is randomly chosen from among theses with a different advisor, and thus
      on average we expect C to be more different from A and B than they are
      from one another.

    Why the math works:
    There are 4 basic scenarios.

    sim(A, B) high ; sim(A, C) low
        This is good! This means similar things are identified as such and
        there is a large separation between similar and dissimilar objects.
        The score metric comes out positive.

    sim(A, B) high ; sim(A, C) high
        This is bad! It means everything is similar to everything, which means
        the model is meaningless (at least for this example). The score metric
        comes out near zero.

    sim(A, B) low ; sim(A, C) low
        Also meaningless; also near zero.

    sim(A, B) low ; sim(A, C) high
        This is very bad! It means the model thinks similar theses are
        dissimilar, and vice versa. This is actively misleading. The score
        metric comes out negative.

    Note that for any individual tuple, there may be low-to-negative results
    even if the overall model is good. Because we haven't hand-inspected the
    theses, we don't know for sure that A/B *should* be similar, or that A/C
    *should* be dissimilar. That's why we use a bunch of tuples - we expect
    this to work on average.

    Note also that the model was NOT trained on who the advisors are (we could
    have used this as a label, but did not). This is important because we don't
    want the metric to be simply measuring how well the model learned known
    inputs. If we were to tell it about advisors, it would successfully
    separate theses with different advisors without necessarily learning
    anything about the semantics of thesis text, and the metric would be
    uninformative.
    """
    def __init__(self, model_list):
        self.model_list = model_list
        self.queryset = self.get_queryset()
        self.tuples = self.choose_tuples()
        self.scores = []
        self.tokenizer = LabeledLineSentence('fake')  # used only for tokenizer

    def get_queryset(self):
        """
        The queryset for the evaluator is the set of files that the neural net
        was *trained* on.

        It's important to restrict ourselves to these, and not to the entire
        universe of theses, because we only get meaningful data from the test
        set about whether the parameters have generalized well if we are
        looking at its performance on training set data.
        """
        matcher = '1721.1-(\d+).txt'
        training_dir = os.path.join(CUR_DIR, FILES_DIR, 'training')
        training_files = os.listdir(training_dir)
        training_ids = [re.match(matcher, filename).groups()[0]
                        for filename in training_files]
        return Thesis.objects.filter(identifier__in=training_ids)

    def choose_tuples(self):
        """Choose up to 50 tuples we can use to evaluate our net."""
        print('Choosing tuples')
        tuples = []

        targets = Contribution.objects.filter(role=Contribution.ADVISOR,
                                              thesis__in=self.queryset)
        advisors = Person.objects.annotate(
            num_theses=Count('contribution__thesis')
        ).filter(
            contribution__in=targets, num_theses__gte=2
        ).distinct()

        count = 0

        for advisor in advisors:
            try:
                a, b = advisor.thesis_set.intersection(self.queryset)[0:2]
            except ValueError:
                # It's possible that, even if an advisor has advised 2 or more
                # theses, that the theses won't all be in our queryset. (For
                # example, some advisors supervise theses in multiple
                # departments.) If we encounter these, just move on to the next
                # option.
                continue

            theses = self.queryset.exclude(contribution__person=advisor)
            c = self.get_random_outsider_thesis(theses)
            tuples.append((a, b, c))
            count += 1

            if count == 50:
                break

        return tuples

    def get_random_outsider_thesis(self, theses):
        num = theses.count()
        while True:
            idx = random.randrange(0, num)
            filename = os.path.join(CUR_DIR, FILES_DIR, 'main',
                                    '1721.1-{}.txt'.format(idx))
            if os.path.isfile(filename):
                c = theses[idx]
                break
        return c

    def get_filename_from_identifier(self, identifier):
        return

    def get_tokens(self, doctag):
        filename = os.path.join(CUR_DIR, FILES_DIR, 'main', doctag)
        with open(filename, 'r') as f:
            doc = f.read()

        return self.tokenizer._tokenize(doc)

    def trained_similarities(self, model, a_label, b_label, c_label):
        a_to_b = model.docvecs.similarity(a_label, b_label)
        a_to_c = model.docvecs.similarity(a_label, c_label)
        b_to_c = model.docvecs.similarity(b_label, c_label)

        return a_to_b, a_to_c, b_to_c

    def untrained_similarities(self, model, a_tokens, b_tokens, c_tokens):
        a_to_b = model.docvecs.similarity_unseen_docs(
            model, a_tokens, b_tokens)
        a_to_c = model.docvecs.similarity_unseen_docs(
            model, a_tokens, c_tokens)
        b_to_c = model.docvecs.similarity_unseen_docs(
            model, b_tokens, c_tokens)

        return a_to_b, a_to_c, b_to_c

    def calculate_score(self, model, training):
        print('Scoring model')
        score = 0

        for tuple in self.tuples:
            a_label = '1721.1-{}.txt'.format(tuple[0].identifier)
            b_label = '1721.1-{}.txt'.format(tuple[1].identifier)
            c_label = '1721.1-{}.txt'.format(tuple[2].identifier)

            a_tokens = self.get_tokens(a_label)
            b_tokens = self.get_tokens(b_label)
            c_tokens = self.get_tokens(c_label)

            # If the documents are in the trained set, use the doc2vec
            # similarity() function. We don't want to use
            # similarity_unseen_docs for both test and training, because it
            # needs to use infer_vector, and the results of that are somewhat
            # unpredictable. In particular, the test data may score *better*
            # than the training data. The vector calculated during training is
            # more accurate and we should use it where available.
            if training:
                a_to_b, a_to_c, b_to_c = self.trained_similarities(
                    model, a_label, b_label, c_label)
            else:
                a_to_b, a_to_c, b_to_c = self.untrained_similarities(
                    model, a_tokens, b_tokens, c_tokens)

            subscore = 2 * a_to_b - a_to_c - b_to_c

            score += subscore

        return score

    def score_models(self):
        for filename in self.model_list:
            fullpath = os.path.join(CUR_DIR, 'nets', filename)
            model = Doc2Vec.load(fullpath)
            training = 'training' in fullpath
            score = self.calculate_score(model, training)

            self.scores.append((filename, score))

        self.scores.sort(key=lambda x: x[1], reverse=True)

    def pretty_print(self):
        print('       Model  |   Score')
        print('------------------------------')
        for scoretuple in self.scores:
            print('{} |   {}'.format(scoretuple[0], scoretuple[1]))
        print('------------------------------')
        print('🌈 🎉 🦄')

    def evaluate(self):
        print('About to score all models')
        self.score_models()
        self.pretty_print()


def write_metadata(args):
    fetcher = DocFetcher()
    fetcher.get_network_files(args)


def train_model(args):
    qs = args['queryset']
    fn = args['filename']
    subdirs = args['subdir_list']

    mt = ModelTrainer(subdirs)
    mt.train_model(fn, qs)

    model_list = os.listdir(os.path.join(CUR_DIR, 'nets'))
    model_list = [x for x in model_list
                  if x.startswith(fn) and x.endswith('.model')]
    evie = Evaluator(model_list)
    evie.evaluate()
