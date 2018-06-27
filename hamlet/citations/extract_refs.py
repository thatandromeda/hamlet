import multiprocessing as mp
import os

from refextract import extract_references_from_string

from django.conf import settings

# If we can extract several of these from a reference, there's a pretty
# good chance it's a legitimate citation.
targets = {
    'doi', 'journal', 'url', 'author', 'title', 'isbn', 'publisher', 'year'
}

localpath = os.path.join(settings.PROJECT_DIR, 'neural', 'files', 'main')


def _inner_find_refs(refdict, goodrefs, badrefs):
    if len(set(refdict.keys()).intersection(targets)) >= 3:
        goodrefs.append(refdict)
    else:
        badrefs.append(refdict)


def find_candidate_refs(reflist):
    if not reflist:
        return [], []

    goodrefs = []
    badrefs = []
    for refs in reflist:
        if isinstance(refs, dict):
            _inner_find_refs(refs, goodrefs, badrefs)
        else:
            for refdict in refs:
                _inner_find_refs(refdict, goodrefs, badrefs)

    return goodrefs, badrefs


# Extract potential references from ends of files. (We don't want to parse
# the beginning, because if the extractor sees "References" or "Bibliography"
# in the table of contents, it may conclude it has found a reference section
# and parse the entire file for references.)
def extract_refs(handle):
    filepath = os.path.join(localpath, handle)
    if os.path.isfile(filepath):
        try:
            popenstring = 'tail -n 1000 {}'.format(filepath)
            end_of_file = os.popen(popenstring).read()
            refs = extract_references_from_string(end_of_file)
            if refs:
                return refs
        except:
            pass


def reprocess_bad(good, bad):
    filteredbad = [refdict for refdict in bad
                   if len(refdict['raw_ref'][0]) < 200]

    morerefs = []
    for x in range(0, len(filteredbad) - 1):
        testref = '{} {}'.format(filteredbad[x]['raw_ref'][0],
                                 filteredbad[x + 1]['raw_ref'][0])
        if len(testref) < 200:
            ref = extract_references_from_string(testref)
            morerefs.append(ref)

    new_good, new_bad = find_candidate_refs(morerefs)

    return new_good, new_bad


def find_all_refs(reflist):
    good_candidates, bad_candidates = find_candidate_refs(reflist)

    # At this point the goodrefs are very good. The badrefs include some
    # goodrefs - particularly in cases where refs have been split over multiple
    # lines. Let's try to extract those.
    new_good, new_bad = reprocess_bad(good_candidates, bad_candidates)

    good_candidates.extend(new_good)
    bad_candidates.extend(new_bad)

    print("Good candidates found: %d" % len(good_candidates))
    print("Bad candidates found: %d" % len(bad_candidates))

    return good_candidates


def extract_good_refs(maxfiles):

    pool = mp.Pool(mp.cpu_count())
    results = pool.map(extract_refs, os.listdir(localpath)[:maxfiles])
    good = find_all_refs(results)

    pool.close()
    pool.join()

    return good
