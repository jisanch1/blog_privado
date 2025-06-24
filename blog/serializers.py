# blog/serializers.py

from rest_framework import serializers
from .models import Post, Comment, Reaction
from django.contrib.auth.models import User
# ¡Nuevas importaciones necesarias para manejar GenericRelations!
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation # Puede que no sea estrictamente necesaria aquí si solo accedes, pero es buena práctica


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author']

    def get_likes_count(self, obj):
        # Accede a las reacciones a través del ContentType del Post y el ID del objeto
        post_content_type = ContentType.objects.get_for_model(Post)
        return Reaction.objects.filter(
            content_type=post_content_type,
            object_id=obj.id,
            is_like=True
        ).count()

    def get_dislikes_count(self, obj):
        post_content_type = ContentType.objects.get_for_model(Post)
        return Reaction.objects.filter(
            content_type=post_content_type,
            object_id=obj.id,
            is_like=False
        ).count()

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author']

    def get_likes_count(self, obj):
        # Accede a las reacciones a través del ContentType del Comment y el ID del objeto
        comment_content_type = ContentType.objects.get_for_model(Comment)
        return Reaction.objects.filter(
            content_type=comment_content_type,
            object_id=obj.id,
            is_like=True
        ).count()

    def get_dislikes_count(self, obj):
        comment_content_type = ContentType.objects.get_for_model(Comment)
        return Reaction.objects.filter(
            content_type=comment_content_type,
            object_id=obj.id,
            is_like=False
        ).count()

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ['id', 'content_type', 'object_id', 'user', 'is_like', 'created_at']
        read_only_fields = ['user']