import json

from django.contrib import messages
from django.test import TestCase, Client
from django.urls import reverse


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_success(self):
        resp = self.client.get(reverse('checker:index'))
        self.assertEqual(resp.status_code, 200)

    def test_messages_validation_error(self):
        data = dict()
        data['url'] = 'test'
        resp = self.client.post(reverse('checker:result'), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertRedirects(resp, reverse('checker:index'))

        msgs = list(resp.context.get('messages'))
        for msg in msgs:
            if msg.level == messages.INFO:
                self.assertEqual(str(msg), f'url={data["url"]}')
            if msg.level == messages.ERROR:
                self.assertEqual(str(msg), 'URL validator error')


class ResultViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_success(self):
        resp = self.client.get(reverse('checker:result'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'result.min.js')

    def test_get_with_debug(self):
        with self.settings(DEBUG=True):
            resp = self.client.get(reverse('checker:result'))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, 'result.js')

    def test_post_valid_data(self):
        data = dict()
        urls = ('example.com', 'http://example.com', 'https://example.com',
                'https://sub.example.com', 'https://example-a-z.com')
        for url in urls:
            data['url'] = url
            resp = self.client.post(reverse('checker:result'), data)
            self.assertEqual(resp.status_code, 200, f'url={url}')

    def test_post_invalid_data(self):
        data = dict()
        urls = ('example', 'ftp://example.com', 'tel:123456789', 'mailto:test@gmail.com',
                'http://test@gmail.com', 'test@gmail.com')
        for url in urls:
            data['url'] = url
            resp = self.client.post(reverse('checker:result'), data, follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertRedirects(resp, reverse('checker:index'), msg_prefix=f'url={url}')
            self.assertContains(resp, 'URL validator error')


class ApiGetStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.path = reverse('checker:api-get-status')

    def test_get_not_allowed(self):
        resp = self.client.get(self.path)
        self.assertEqual(resp.status_code, 400)

    def test_post_valid_url(self):
        data = dict()
        data['url'] = 'https://example.com'
        resp = self.client.post(self.path, data)
        self.assertEqual(resp.status_code, 200)

        content = json.loads(resp.content)
        content_data = content['data']
        self.assertIsNone(content['error'])
        self.assertEqual(content_data['status'], 200)
        self.assertIn('time', content_data)
        self.assertEqual(content_data['url'], data['url'])

    def test_post_invalid_url(self):
        data = dict()
        data['url'] = 'example.com'
        resp = self.client.post(self.path, data)
        self.assertEqual(resp.status_code, 200)

        content = json.loads(resp.content)
        content_data = content['data']
        self.assertIsNotNone(content['error'])
        self.assertNotIn('status', content_data)
        self.assertNotIn('time', content_data)
        self.assertEqual(content_data['url'], data['url'])

    def test_post_url_not_found(self):
        data = dict()
        data['url'] = 'https://example.com/404'
        resp = self.client.post(self.path, data)
        self.assertEqual(resp.status_code, 200)

        content = json.loads(resp.content)
        content_data = content['data']
        self.assertIsNotNone(content['error'])
        self.assertNotEqual(content_data['status'], 200)
        self.assertIn('time', content_data)
        self.assertEqual(content_data['url'], data['url'])
