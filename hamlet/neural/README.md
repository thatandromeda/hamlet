There's a lot going on in `train_neural_net.py`, some of which will need to be modified or rewritten to stand up HAMLET on another data set. Here's an explanation. It also points toward the things you are most likely to need to rewrite. (The original HAMLET was working with a 1.7 or 1.8 version of DSpace with a lot of local customizations, so your repository is definitely different.)

The overall process is:
* `DocFetcher` queries the repository to figure out which files are theses, and creates `Thesis` objects in the Django db accordingly;
* `MetadataWriter` parses metadata records from the repository to update the `Thesis` instances;
* `ModelTrainer` preprocesses text files (checking for their existence and then, if necessary, pulling them from the repository and OCRing them) and trains a neural net;
* `Evaluator` chooses which of several candidate neural nets (i.e. trained with different hyperparameters) is best.

You can route around `DocFetcher` and `MetadataWriter` entirely if you have some other mechanism for getting data into your `Thesis` objects, as `ModelTrainer` accepts a queryset of `Thesis` objects.

# General changes for your environment
Check that `METS_NAMESPACE` is correct for your records.

There are lots of hardcoded instances of `1721.1` -- this is a magic number in many MIT records (a handle.net prefix); you likely have different magic numbers.

# `DocFetcher`
This class:
* fetches a list of candidate files from a repository (`get_record_list`);
* parses that list to extract file handles, file identifiers, and setSpecs (which indicate what if any collections within the repository a given record belongs to; `parse_record_list`);
* checks to see if it has already processed the file;
* checks to see if the file is a thesis (`is_thesis`);
* fetches and processes the file (`get_single_network_file`)
    - This first checks whether the file is already in the django database
    - It also gets the associated metadata record (`get_record`)
    - And stores the metadata (`write_metadata`)

It runs the entire above process through `get_network_files`.

It expects to have the following environment variables set:
* `DSPACE_OAI_IDENTIFIER`
* `DSPACE_OAI_URI`

## For your environment
`get_record_list`, `get_record`, and `parse_record_list` make assumptions about the repository API and record structure. These assumptions may not be true for you.

# `MetadataWriter`
This class extracts the metadata we want to store in the database from the repository metadata records. To wit:

```
authors = dc.findall('.//dc:creator', METS_NAMESPACE)
advisors, departments = self.extract_contributors(dc)
date = self.extract_date(dc)
degree = self.extract_degree(mets, item_sets)
id = self.extract_identifier(dc)
title = self.extract_title(mets)
url = self.extract_url(mets)
```

## For your environment
If your records are lacking any of this information, you will need to:
* update `MetadataWriter` so it doesn't look for that information;
* ensure `theses.models.Thesis` does not require those fields;
* make changes to the front end so it isn't trying to display that information

You will also want to look at each of the `extract_` functions to make sure they actually match your record syntax. (Or at least try it on a few records and see if it works.)

You should verify that `MetadataWriter.DEGREE_OPTIONS` matches the way degrees are indicated in your records.

`extract_contributors` and `extract_degree` contain some text processing that is specific to MIT and will need to be changed for your institution.

This references `THESIS_SET_LIST` (which pulls data from `thesis_set_list.json`); this is a list of names of thesis sets available in the repository and will definitely need to be changed for other institutions.

# ModelTrainer
Invoked via `train_model`, which:
* sources text for theses;
* splits texts into test and training examples;
* actually trains the neural nets
    - Yes, plural; the nested `for window...` and `for step...` loops are training with different hyperparameters.

`extract_text` will:
* check to see if the extracted file is already present for a given `Thesis`;
* if not:
    - fetch a pdf from the `url` attribute of the `Thesis` object (this will have been populated by `MetadataWriter` and `DocFetcher` earlier);
    - OCR it;
    - update the `unextractable` property of the `Thesis` object according to its success with OCR;
    - write the OCR text to the files area.

# For your environment
You can train with different (possibly fewer) hyperparameters by adjusting the nested for loops in `train_model`. (If your training set doesn't have Advisors you may only want to train one model; see `Evaluator`.)

`ModelTrainer` expects to find a directory named `files` with a subdirectory named `main` (unless it has been instantiated with different `files_subdirs`). If thesis text files live somewhere else in your environment, change this.

# LabeledLineSentence
This tokenizes documents. You don't need to change it. You may want to change it because the tokenization is incredibly half-assed, but you don't *need* to change it to get things working.
