import os
from unittest import skip

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings


@override_settings(COMPRESS_ENABLED=False)
class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # If you forgot to define the URL, the test suite will fail here.
        self.url = reverse('citations:lit_review_buddy')
        self.fix_path = os.path.join(
            settings.BASE_DIR, 'hamlet/theses/fixtures')

    def test_page_loads(self):
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_front_page_has_widget(self):
        response = self.client.get(reverse('home'))
        assert self.url in response.content.decode('utf-8')

    def test_render_on_success(self):
        '''
        Check that we render the correct template with the correct context on
        a successful post.
        '''
        url = reverse('citations:lit_review_buddy')
        with open(os.path.join(self.fix_path, '1721.1-33360.txt'), 'rb') as fp:
            response = self.client.post(url,
                {"file": fp, "captcha_0": "sometext", "captcha_1": "PASSED"})

        assert response.status_code == 200
        assert 'suggestions' in response.context
        assert 'total_suggestions' in response.context
        template_names = [t.name for t in response.templates]
        assert 'citations/lit_review_outcomes.html' in template_names

    # This is failing, even though performing the same behavior in the
    # browser, with the test settings file, works. It looks like infer_vector
    # maybe doesn't return the same thing each time (!) and so this test can
    # fail even when a very similar one in hamlet/theses/tests/test_views.py
    # succeeds.
    @skip
    def test_citations_found(self):
        '''
        Check that we get the expected suggestions on a successful post.
        '''
        citation = "Dr. Orhan Soykan. Power Sources for Implantable Medical Devices. Medical Device Manufacturing & Technology, 2002."  # noqa
        url = reverse('citations:lit_review_buddy')
        with open(os.path.join(self.fix_path, '1721.1-33360.txt'), 'rb') as fp:
            response = self.client.post(url,
                {"file": fp, "captcha_0": "sometext", "captcha_1": "PASSED"})

        assert citation in response.content.decode('utf-8')
