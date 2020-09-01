from django.test import TestCase
from django.test import Client
from django.urls import reverse
from posts.models import User


class UserTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_user(self):
        self.client.post(
            reverse('signup'),
            {
                'username': 'testuser',
                'password1': 'asdf6689sdf',
                'password2': 'asdf6689sdf'
                },
            follow=True)
        response = self.client.get(
            reverse('profile', kwargs={'username': 'testuser'})
        )
        self.assertIsInstance(response.context['author'], User)
        self.assertEqual(response.status_code, 200)
