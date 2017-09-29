import argparse
import os
from string import punctuation, Template
import subprocess
import sys
import time

from gensim.models.doc2vec import LabeledSentence, Doc2Vec
from nltk import sent_tokenize, WordPunctTokenizer

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


class LabeledLineSentence(object):
    def __init__(self, doc_list, docs_dir):
        self.doc_list = doc_list
        self.DOCS_ABSOLUTE_DIR = docs_dir

    def __iter__(self):
        for doc in self.doc_list:
            yield LabeledSentence(words=self._prep_document(doc), tags=[doc])

    def _prep_document(self, doc):
        """Given a document filename, opens the file and tokenizes it."""
        full_path = os.path.join(self.DOCS_ABSOLUTE_DIR, doc)
        with open(full_path, 'r') as doc_contents:
            return self._tokenize(doc_contents.read())

    def _tokenize(self, doc):
        all_tokens = []
        sentences = sent_tokenize(doc)

        tokenizer = WordPunctTokenizer()
        for sentence in sentences:
            words = tokenizer.tokenize(sentence.lower())
            words = [word for word in words if word not in punctuation]
            all_tokens.extend(words)
        return all_tokens


class ModelTrainer(object):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOCS_RELATIVE_DIR = 'documents'
    DOCS_ABSOLUTE_DIR = os.path.join(BASE_DIR, DOCS_RELATIVE_DIR)
    KERB = 'm31'

    def execute(self, args):
        if args.kerb:
            self.KERB = args.kerb

        if args.network:
            self.get_network_files(args.network)

        self.train_model(args.filename)

    def get_iterator(self):
        doc_list = [f for f in os.listdir(self.DOCS_ABSOLUTE_DIR)
                    if os.path.splitext(f)[-1] == '.txt']
        return LabeledLineSentence(doc_list, self.DOCS_ABSOLUTE_DIR)

    def get_network_files(self, netdir):
        """Given a subdirectory name (presumed to be of the repo-dev-1.mit.edu
        thesis directory), get its .xml and .txt files and deposit them into
        DOCS_ABSOLUTE_DIR + subdirectory name. Requires that ssh keypair auth
        be already set up."""
        if netdir not in THESIS_SUBDIRS:
            sys.exit('Unrecognized network directory. -n must be in '
                '{subdirs}'.format(subdirs=THESIS_SUBDIRS))

        working_dir = os.path.join(self.DOCS_ABSOLUTE_DIR, netdir)
        self.DOCS_ABSOLUTE_DIR = working_dir

        # Make sure directory exists but is empty
        try:
            contents = os.listdir(working_dir)
            if contents:
                sys.exit("The specified directory is not empty; exiting to "
                    "avoid overwriting files. If you'd like to write files to "
                    "this directory, please empty it and rerun the script.")
        except FileNotFoundError:
            os.makedirs(working_dir)

        cmd1 = Template("ssh $kerb@repo-dev-1.mit.edu \"find /mnt/tdm/rich/expansions/$netdir/ -name '*-new.txt' -or -name '*.xml' > tempfile.txt\"")  # noqa
        cmd2 = Template("ssh $kerb@repo-dev-1.mit.edu \"tar -czvf tempfile.tar.gz -T tempfile.txt\"")
        cmd3 = Template("scp $kerb@repo-dev-1.mit.edu:tempfile.tar.gz $working_dir")  # noqa
        cmd4 = Template("cd $working_dir ; tar -xzvf tempfile.tar.gz -s '|.*/||'")
        cmd5 = Template("ssh $kerb@repo-dev-1.mit.edu rm 'tempfile.*'")

        print("Identitying target network files...")
        subprocess.run(cmd1.substitute(kerb=self.KERB, netdir=netdir),
                       shell=True)

        print("Making archive...")
        subprocess.run(cmd2.substitute(kerb=self.KERB), shell=True)

        print("Getting archive...")
        subprocess.run(cmd3.substitute(kerb=self.KERB,
                       working_dir=working_dir), shell=True)

        print("Expanding archive...")
        subprocess.run(cmd4.substitute(working_dir=working_dir), shell=True)

        print("Cleaning up...")
        subprocess.run(cmd5.substitute(kerb=self.KERB), shell=True)

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
    parser.add_argument('-n', '--network', help="Get files from the specified "
        "thesis subdirectory of repo-dev-1.mit.edu. Requires that you have "
        "ssh keypair auth configured.")
    parser.add_argument('-k', '--kerb', help="Your kerberos ID. Defaults to "
        "m31.")

    args = parser.parse_args()
    ModelTrainer().execute(args)
