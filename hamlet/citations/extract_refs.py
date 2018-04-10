import multiprocessing as mp
import os
import pickle

from refextract import extract_references_from_string

from django.conf import settings

# If we can extract several of these from a reference, there's a pretty
# good chance it's a legitimate citation.
targets = {
    'doi', 'journal', 'url', 'author', 'title', 'isbn', 'publisher', 'year'
}

localpath = os.path.join(settings.PROJECT_DIR, 'neural', 'files', 'main')


# Categorizing references as good or bad ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def _classify_ref(handle, refdict, goodrefs, badrefs):
    # Determine whether a given candidate citation should be categorized as
    # good or bad.
    #
    # :param handle: The filename of the current thesis.
    # :type handle: str
    # :param refdict: A dictionary representing a single candidate citation.
    # :type refdict: dict
    # :param goodrefs: The current believed-good citations.
    # :type goodrefs: dict. Its keys are handles; its values are lists of
    #                 dicts.
    # :param badrefs: The current believed-bad citations.
    # :type badrefs: dict. Per goodrefs.
    # :rtype: dict
    # :rtype: dict
    if len(set(refdict.keys()).intersection(targets)) >= 3:
        goodrefs.setdefault(handle, []).append(refdict)
    else:
        badrefs.setdefault(handle, []).append(refdict)

    return goodrefs, badrefs


def _verify_reftuple_format(reftuples):
    # Ensure that reftuples has the data structure we expect.
    # This is a smoke test - it's just checking the first member, not all of
    # them.
    assert isinstance(reftuples, list)
    first_tuple = reftuples[0]
    assert isinstance(first_tuple, tuple)
    assert isinstance(first_tuple[0], str)
    assert isinstance(first_tuple[1], list)
    assert isinstance(first_tuple[1][0], dict)


def _find_candidate_refs(reftuples):
    # Given citation data associated with various filenames, classify the
    # citations as good or bad.
    #
    # :param reftuples: list of tuples of (filename, list of dictd of citation
    # data).
    # :rtype: two dicts. Each dict has filenames as keys; its values are lists
    # of dicts of citation data.
    if not reftuples:
        return {}, {}

    goodrefs = {}
    badrefs = {}

    for reftuple in reftuples:
        handle = reftuple[0]
        reflist = reftuple[1]
        for refdict in reflist:
            goodrefs, badrefs = \
                _classify_ref(handle, refdict, goodrefs, badrefs)

    return goodrefs, badrefs


def _reprocess_bad(good, bad):
    for handle in bad.keys():
        filteredbad = [refdict for refdict in bad[handle]
                       if refdict and len(refdict['raw_ref'][0]) < 200]

        for x in range(0, len(filteredbad) - 1):
            testref = '{} {}'.format(filteredbad[x]['raw_ref'][0],
                                     filteredbad[x + 1]['raw_ref'][0])
            if len(testref) < 200:
                ref = extract_references_from_string(testref)

                local_good, local_bad = _find_candidate_refs([(handle, ref)])
                good.setdefault(handle, []).append(local_good)
                bad.setdefault(handle, []).append(local_bad)

    return good, bad


def _find_good_refs(reftuples):
    # Given a list of tuples of (filename, list of citation data dicts),
    # find the probably good citation data.
    #
    # :param reftuples: A list of 2-tuples. Each tuple is (filename, list of
    # candidate references). Each candidate reference is a dict.
    # :rtype: dict. The keys of the dict are filenames; the values are lists of
    # dicts of believed-good citation data.
    _verify_reftuple_format(reftuples)

    good_candidates, bad_candidates = _find_candidate_refs(reftuples)

    # At this point the goodrefs are very good. The badrefs include some
    # goodrefs - particularly in cases where refs have been split over multiple
    # lines. Let's try to extract those.
    new_good, new_bad = _reprocess_bad(good_candidates, bad_candidates)

    print("Theses with good candidates: %d" % len(new_good))
    print("Theses with bad candidates: %d" % len(new_bad))

    print("Total good candidates: %d" %
        sum([len(x) for x in new_good.values()]))
    print("Total bad candidates: %d" %
        sum([len(x) for x in new_bad.values()]))

    return new_good


# Extracting references from files ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def _extract_refs(handle):
    # Extract potential references from ends of files. Return a tuple of
    # the file handle and the candidate references (a list of dicts).
    #
    # We don't want to parse the beginning, because if the extractor sees
    # "References" or "Bibliography" in the table of contents, it may conclude
    # it has found a reference section and parse the entire file for
    # references, which is unacceptably time-consuming.
    #
    # :param handle: name of a file containing thesis text (not the full path,
    # just the name).
    # :type handle: str.
    # :rtype: tuple or None
    filepath = os.path.join(localpath, handle)
    if os.path.isfile(filepath):
        try:
            popenstring = 'tail -n 1000 {}'.format(filepath)
            end_of_file = os.popen(popenstring).read()
            # The 'is_only_references' flag for this function, when False, is
            # supposed to increase accuracy for text that may contain things
            # other than the reference section (as ours does). It doesn't
            # seem to work, however.
            refs = extract_references_from_string(end_of_file)
            if refs:
                return (handle, refs)
        except:
            pass


# The main function ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def extract_good_refs(maxfiles):
    # Extracts believed-good citations from files and returns them.
    # Along the way pickles the extracted but unprocessed refs to simplify
    # debugging and future processing (the extraction is the time-consuming
    # step, so we persist its results.)
    #
    # :param maxfiles: The maximum number of files to extract data from.
    # (Extracting citations from all 43K+ theses takes days, even parallelized,
    # so a shorter option is provided for testing purposes.)
    # :type maxfiles: int
    # :rtype: dict. The keys of the dict are filenames; the values are lists of
    # dicts of believed-good citation data.

    # Extract refs from files ----------------
    pool = mp.Pool(mp.cpu_count())
    if not maxfiles:
        file_list = os.listdir(localpath)
    else:
        file_list = os.listdir(localpath)[:maxfiles]

    results = pool.map(_extract_refs, file_list)

    # Even at 8 cores this data takes days to extract, so persist it now -
    # that way if there are any problems with the subsequent steps, you can
    # recover.
    pickle.dump(results, open("refs.p", "wb"))

    pool.close()
    pool.join()

    # Find good refs -------------------------
    good = _find_good_refs(results)

    return good
