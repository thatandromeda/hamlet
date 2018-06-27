from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings


@override_settings(COMPRESS_ENABLED=False)
class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # If you forgot to define the URL, the test suite will fail here.
        self.url = reverse('citations:lit_review_buddy')

    def test_page_loads(self):
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_front_page_has_widget(self):
        response = self.client.get(reverse('home'))
        assert self.url in response.content.decode('utf-8')
