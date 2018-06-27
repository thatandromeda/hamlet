# There are several ways that we could end up with variant name forms for the
# same person. These scripts identify several common variant types. They are
# intended to be run manually so that variants can be fixed manually.
import re

from hamlet.theses.models import Person, Contribution


def _get_author_lastname(name):
    expr = r'^[\w\-\']*,'
    match = re.match(expr, name)
    if match:
        retval = match.group(0)
    else:
        retval = None

    return retval


def _get_candidates_from_names(name, lastname):
    first_initial = name.split(',')[1].strip()[0]
    return Person.objects.filter(
        name__iendswith=lastname, name__istartswith=first_initial)


# The problem: name formats are different for advisors and for authors (the
# formats are 'first last' and 'last, first' respectively). This means that the
# same person can have different names, and thus be represented by different
# database instance, if they have been both an MIT undergrad and an MIT
# professor. It would be better if they were the same instance.
#
# This script finds possible duplicates and flags them for manual attention.
def find_author_advisor_dupes():
    for p in Person.objects.all():
        name = p.name
        lastname = _get_author_lastname(name)
        if not lastname:
            continue

        candidates = _get_candidates_from_names(name, lastname)

        if candidates:
            print("Check {}".format(name))


def _check_first_mi_last_form(name):
    expr = r'([\w\-\']*) [\w]\. ([\w\-\']*)'
    match = re.match(expr, name)
    if match:
        firstname = match.group(1)
        lastname = match.group(2)
        firstlast = "{} {}".format(firstname, lastname)
        persons = Person.objects.filter(name=firstlast)

        if persons:
            print("Check {}".format(name))
            return True
    return False


def _check_fi_last_form(name):
    expr = r'([\w\-\']\.) ([\w\-\']*)'
    match = re.match(expr, name)
    if match:
        firstinitial = match.group(1)
        lastname = match.group(2)
        persons = Person.objects.filter(
            name__startswith=firstinitial, name__endswith=lastname)

        if persons:
            print("Check {}".format(name))
            return True
    return False


def _check_fi_middle_last_form(name):
    expr = r'([\w\-\']\.) [\w\-\']* ([\w\-\']*)'
    match = re.match(expr, name)
    if match:
        firstinitial = match.group(1)
        lastname = match.group(2)
        persons = Person.objects.filter(
            name__startswith=firstinitial, name__endswith=lastname)

        if persons:
            print("Check {}".format(name))
            return True
    return False


# This checks for a couple of variant spelling formats. If any of them
# succeed, we continue rather than doing the other checks - we already know
# we need to check this name and other variants will come up when fixing
# manually.
def find_advisor_variant_spellings():
    for p in Person.objects.all():
        name = p.name
        if _check_first_mi_last_form(name):
            continue

        if _check_fi_last_form(name):
            continue

        _check_fi_middle_last_form(name)


# This takes all theses advised or authored by 'old' and updates that
# contribution to point at 'new'. It does not change the role (author/advisor).
# This is useful for rectifying variant spellings.
def switch_contributors(old_pk, new_pk):
    assert old_pk != new_pk
    old = Person.objects.get(pk=old_pk)
    new = Person.objects.get(pk=new_pk)
    Contribution.objects.filter(person=old).update(person=new)
    old.delete()


def _names_look_like_people(names):
    expr = r'[\w\-]*\.? [\w\-]*'
    return all([
        re.match(expr, names[0].strip()),
        re.match(expr, names[1].strip()),
    ])


# This finds all Person instances which may actually represent multiple
# people. This can happen when an XML field contained multiple names separated
# by commas.
def find_multiples():
    for p in Person.objects.all():
        names = p.name.split(',')
        if len(names) > 1 and _names_look_like_people(names):
            print("{} may contain multiple names".format(p.name))
