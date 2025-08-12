from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import SimpleTestCase

from .models import Post, Comment, Reaction


class PostViewSetTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.post = Post.objects.create(title="First Post", content="Content", author=self.user1)

    def test_post_list(self):
        Post.objects.create(title="Second Post", content="More", author=self.user2)
        response = self.client.get("/api/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_post_creation_requires_authentication(self):
        data = {"title": "New", "content": "New content"}
        response = self.client.post("/api/posts/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_creation_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        data = {"title": "Authorized", "content": "Auth content"}
        response = self.client.post("/api/posts/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["username"], self.user1.username)

    def test_post_update_permissions(self):
        url = f"/api/posts/{self.post.id}/"
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(url, {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(url, {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")


class CommentViewSetTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.post = Post.objects.create(title="Post", content="Content", author=self.user1)
        self.comment = Comment.objects.create(post=self.post, author=self.user1, content="Hi")

    def test_comment_creation_requires_authentication(self):
        data = {"post": self.post.id, "content": "Nice"}
        response = self.client.post("/api/comments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comment_creation_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        data = {"post": self.post.id, "content": "Nice"}
        response = self.client.post("/api/comments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["username"], self.user1.username)

    def test_comment_update_permissions(self):
        url = f"/api/comments/{self.comment.id}/"
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(url, {"content": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(url, {"content": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Updated")


class ReactionViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass123")
        self.post = Post.objects.create(title="Post", content="Content", author=self.user)
        self.ct = ContentType.objects.get_for_model(Post)
        self.url = "/api/reactions/"
        self.data = {"content_type": self.ct.id, "object_id": self.post.id, "is_like": True}

    def test_reaction_requires_authentication(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_like(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reaction.objects.count(), 1)

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_toggle_like_to_dislike(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url, self.data, format="json")
        dislike = self.data.copy()
        dislike["is_like"] = False
        response = self.client.post(self.url, dislike, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reaction.objects.count(), 1)
        self.assertFalse(Reaction.objects.first().is_like)


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="authuser", password="pass123")

    def test_obtain_token_and_create_post(self):
        response = self.client.post("/api/token-auth/", {"username": "authuser", "password": "pass123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.post("/api/posts/", {"title": "Token", "content": "Content"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["username"], "authuser")


class IndexPageTests(SimpleTestCase):
    def test_index_returns_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blog Privado")

