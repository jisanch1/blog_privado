# blog/serializers.py

from rest_framework import serializers
from .models import Post, Comment, Reaction
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    dislikes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    dislikes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author']

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ['id', 'content_type', 'object_id', 'user', 'is_like', 'created_at']
        read_only_fields = ['user']