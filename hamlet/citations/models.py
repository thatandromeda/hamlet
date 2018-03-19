from django.db import models

from hamlet.theses.models import Thesis


class Citation(models.Model):
    doi = models.CharField(max_length=66)
    journal = models.TextField()
    url = models.URLField()
    author = models.TextField()
    title = models.TextField()
    isbn = models.CharField(max_length=20)
    publisher = models.CharField(max_length=32)
    year = models.CharField(max_length=4)
    raw_ref = models.TextField()

    # Ultimately this will want to be a many-to-many relationship with
    # Thesis. However, right now Thesis metadata is in a somewhat broken
    # state, and it will be easier to fix if we maintain the option of dumping
    # the production Thesis table into the test one and going from there.
    # Citations can't be ManyToMany with Theses before metadata cleanup
    # happens on the citation side anyway, so putting the relationship here
    # doesn't block anything.
    thesis = models.ForeignKey(Thesis)
