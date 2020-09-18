from django.db import models

from hamlet.theses.models import Thesis


class Citation(models.Model):
    doi = models.CharField(max_length=66, blank=True)
    journal = models.TextField(blank=True)
    url = models.URLField(blank=True)
    author = models.TextField(blank=True)
    title = models.TextField(blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=32, blank=True)
    year = models.CharField(max_length=4, blank=True)
    raw_ref = models.TextField()

    # Ultimately this will want to be a many-to-many relationship with
    # Thesis. However, right now Thesis metadata is in a somewhat broken
    # state, and it will be easier to fix if we maintain the option of dumping
    # the production Thesis table into the test one and going from there.
    # Citations can't be ManyToMany with Theses before metadata cleanup
    # happens on the citation side anyway, so putting the relationship here
    # doesn't block anything.
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)

    def __str__(self):
        return self.raw_ref

    class Meta:
        ordering = ['raw_ref']
