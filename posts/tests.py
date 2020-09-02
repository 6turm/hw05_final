from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from .models import Post, User, Group, Follow


class PostTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser')
        self.client.force_login(self.user)
        self.client_anon = Client()
        self.group = Group.objects.create(title='gr_title', slug='gr_slug')

    def test_make_post_auth_client(self):
        text = 'pasta'
        response = self.client.post(
            reverse('new_post'),
            {'group': self.group.id, 'text': text},
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pasta')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, self.group)

    def test_make_post_anonimus(self):
        self.client_anon.post(
            reverse('new_post'), {'text': 'pasta'})
        response = self.client_anon.get(reverse('new_post'))
        redir_url = reverse('login')
        redir_url_next = reverse('new_post')
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'{redir_url}?next={redir_url_next}'
            )

    def test_new_post(self):
        text = 'pasta'
        post = Post.objects.create(
            text=text, author=self.user, group=self.group
            )
        urls = [
            reverse(
                'post',
                kwargs={'username': self.user.username, 'post_id': post.pk}
                ),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('index'),
            reverse('group', kwargs={'slug': self.group.slug})
        ]
        for url in urls:
            self.url_returns(url, self.client, text, self.group, self.user)

    def url_returns(self, url, client, text, group, author):
        response = client.get(url)
        if 'page' in response.context:
            post = response.context['page'].object_list[0]
        else:
            post = response.context['post']

        self.assertEqual(post.text, text)
        self.assertEqual(post.group, group)
        self.assertEqual(post.author, author)

    def test_change_post(self):
        post = Post.objects.create(
            text='pasta',
            author=self.user,
            group=self.group
            )
        text_new = 'pizza'
        group_new = Group.objects.create(title='gr_title2', slug='gr_slug2')
        post_url = reverse(
            'post_edit',
            kwargs={'username': self.user.username, 'post_id': post.id}
            )
        self.client.post(
            post_url,
            {'text': text_new, 'group': group_new.id},
            follow=True
            )
        group_url = reverse('group', kwargs={'slug': self.group.slug})
        response = self.client.get(group_url)
        self.assertNotContains(response, text_new)
        urls = [
            reverse(
                'post',
                kwargs={'username': self.user.username, 'post_id': post.pk}
                ),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('index'),
            reverse('group', kwargs={'slug': group_new.slug})
        ]
        for url in urls:
            self.url_returns(url, self.client, text_new, group_new, self.user)

    def test_404(self):
        response = self.client.get('/not_page/')
        self.assertEqual(response.status_code, 404)

    def test_img_in_other_pages(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            name='img.gif',
            content=small_gif,
            content_type='image/gif',
        )
        post = Post.objects.create(
            text='text with image', author=self.user,
            image=img, group=self.group
        )
        urls = [
            reverse('index'),
            reverse('group', kwargs={'slug': self.group.slug}),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse(
                'post',
                kwargs={'username': self.user.username, 'post_id': post.id}
            ),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, '<img ')

    def test_no_image_file(self):
        no_img = SimpleUploadedFile(
            name='some.txt',
            content=b'asdf',
            content_type='text/plain',
        )
        url = reverse('new_post')
        response = self.client.post(
            url, {'text': 'some text', 'image': no_img}, follow=True
        )
        self.assertFormError(
            response, 'form', 'image',
            errors='Загрузите правильное изображение. Файл, который вы '
            'загрузили, поврежден или не является изображением.'
        )

    def test_cache(self):
        self.client.get(reverse('index'))
        Post.objects.create(text='check text', author=self.user)
        response1 = self.client.get(reverse('index'))
        self.assertNotContains(response1, 'check text')
        cache.clear()
        response2 = self.client.get(reverse('index'))
        self.assertContains(response2, 'check text')

    def test_follow(self):
        author = User.objects.create_user(username='foll_author')
        author_url = reverse('profile', kwargs={'username': author.username})
        follow_url = reverse(
            'profile_follow', kwargs={'username': author.username}
        )

        response = self.client.get(author_url)
        self.assertContains(response, follow_url)

        self.client.get(follow_url)
        following = Follow.objects.filter(
            user__username=self.user, author__username=author
            ).exists()
        self.assertTrue(following)

    def test_unfollow(self):
        author = User.objects.create_user(username='foll_author')
        Follow.objects.create(user=self.user, author=author)

        author_url = reverse('profile', kwargs={'username': author.username})
        unfollow_url = reverse(
            'profile_unfollow', kwargs={'username': author.username}
        )

        response = self.client.get(author_url)
        self.assertContains(response, unfollow_url)

        self.client.get(unfollow_url)
        following = Follow.objects.filter(
            user__username=self.user, author__username=author
            ).exists()
        self.assertFalse(following)

    def test_follow_feed(self):
        author = User.objects.create_user(username="author")
        user_follow = User.objects.create(username="user_follow")
        client_follow = Client()
        client_follow.force_login(user_follow)
        Follow.objects.create(user=user_follow, author=author)
        text = 'some_text'
        Post.objects.create(
            text=text, author=author, group=self.group
            )
        url = reverse('follow_index')

        self.url_returns(url, client_follow, text, self.group, author)

    def test_unfollow_feed(self):
        author = User.objects.create_user(username="author")
        text = 'some_text'
        Post.objects.create(
            text=text, author=author, group=self.group
            )
        url = reverse('follow_index')
        response = self.client.get(url)
        self.assertEqual(len(response.context['page']), 0)

    def test_auth_comment(self):
        text = 'some_post'
        text_comm = 'some_comment'
        post = Post.objects.create(
            text=text, author=self.user, group=self.group
            )

        url_post = reverse(
            'post',
            kwargs={'username': post.author.username, 'post_id': post.pk}
        )
        url_comment = reverse(
                'add_comment',
                kwargs={'username': post.author.username, 'post_id': post.pk}
                )

        self.client.post(url_comment, {'text': text_comm}, follow=True)
        response = self.client.get(url_post)
        comment = response.context['comments'][0]
        self.assertEqual(comment.text, text_comm)
        self.assertEqual(comment.author, self.user)

    def test_anon_comment(self):
        text = 'some_post'
        text_comm = 'some_comment'
        post = Post.objects.create(
            text=text, author=self.user, group=self.group
            )
        url_post = reverse(
            'post',
            kwargs={'username': post.author.username, 'post_id': post.pk}
        )
        url_comment = reverse(
                'add_comment',
                kwargs={'username': post.author.username, 'post_id': post.pk}
                )

        self.client_anon.post(url_comment, {'text': text_comm}, follow=True)
        response = self.client.get(url_post)
        self.assertNotContains(response, text_comm)
