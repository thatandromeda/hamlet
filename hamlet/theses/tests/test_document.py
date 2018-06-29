import os

from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.test import SimpleTestCase

from hamlet.common.document import DocxDocument, factory


class DocumentTestCase(SimpleTestCase):
    fixtures = os.path.join(settings.BASE_DIR, 'hamlet/theses/fixtures')

    def test_factory_returns_document_object(self):
        with open(os.path.join(self.fixtures, 'thesis.txt'), 'rb') as fp:
            doc = factory(UploadedFile(fp))
            assert doc.words[0] == 'Since'
            assert doc.words[-1] == 'fluids.'

    def test_docx_document_returns_words(self):
        with open(os.path.join(self.fixtures, 'thesis.docx'), 'rb') as fp:
            doc = DocxDocument(UploadedFile(fp))
            assert doc.words[0] == 'Time'
            assert doc.words[-1] == 'oneself.'
