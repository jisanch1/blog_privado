from rest_framework import serializers
from .models import Post, Comment, Reaction
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    # Este serializador es para mostrar información básica del usuario (autor de posts/comentarios)
    class Meta:
        model = User
        fields = ['id', 'username'] # Solo exponemos el ID y el nombre de usuario

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True) # Usa el UserSerializer para el autor
    # Incluimos un campo para el número de likes/dislikes (lo calcularemos más adelante)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author'] # El autor se asignará automáticamente en la vista

    def get_likes_count(self, obj):
        # Contar reacciones de "Me Gusta" para este post
        return obj.reaction_set.filter(is_like=True).count()

    def get_dislikes_count(self, obj):
        # Contar reacciones de "No Me Gusta" para este post
        return obj.reaction_set.filter(is_like=False).count()

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    # Incluimos un campo para el número de likes/dislikes (lo calcularemos más adelante)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'likes_count', 'dislikes_count']
        read_only_fields = ['author'] # El autor se asignará automáticamente en la vista

    def get_likes_count(self, obj):
        # Contar reacciones de "Me Gusta" para este comentario
        # Nota: usamos reaction_set aquí porque Reaction tiene una GenericForeignKey
        # La relación inversa se llama 'reaction_set' por defecto
        return obj.reaction_set.filter(is_like=True).count()

    def get_dislikes_count(self, obj):
        # Contar reacciones de "No Me Gusta" para este comentario
        return obj.reaction_set.filter(is_like=False).count()

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # El usuario que reacciona
    # `content_object` es una GenericForeignKey, la cual no es serializable directamente por ModelSerializer.
    # En una API, usualmente envías el ID del objeto y su tipo, no el objeto completo anidado.
    # Para simplificar, aquí nos enfocamos en crear la reacción, no en ver el objeto completo al que reacciona.

    class Meta:
        model = Reaction
        fields = ['id', 'content_type', 'object_id', 'user', 'is_like', 'created_at']
        read_only_fields = ['user'] # El usuario se asignará automáticamente en la vista
