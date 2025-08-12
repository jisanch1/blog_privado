# blog/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post, Comment, Reaction
from .serializers import PostSerializer, CommentSerializer, ReactionSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q

# Permisos personalizados
class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Permite acceso de lectura a todos, pero solo el autor puede editar/borrar.
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura son permitidos para cualquier request GET, HEAD o OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        # Los permisos de escritura solo son permitidos para el autor del objeto
        return obj.author == request.user

class IsReactionOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite acceso de lectura a todos, pero solo el creador de la reacción puede borrarla.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        return Post.objects.annotate(
            likes_count=Count('reactions', filter=Q(reactions__is_like=True)),
            dislikes_count=Count('reactions', filter=Q(reactions__is_like=False)),
        )

    def perform_create(self, serializer):
        # Asigna automáticamente el usuario autenticado como autor del post
        serializer.save(author=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        return Comment.objects.annotate(
            likes_count=Count('reactions', filter=Q(reactions__is_like=True)),
            dislikes_count=Count('reactions', filter=Q(reactions__is_like=False)),
        )

    def perform_create(self, serializer):
        # Asigna automáticamente el usuario autenticado como autor del comentario
        serializer.save(author=self.request.user)

class ReactionViewSet(viewsets.ModelViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsReactionOwnerOrReadOnly] # Solo usuarios autenticados pueden crear reacciones

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_type = serializer.validated_data['content_type']
        object_id = serializer.validated_data['object_id']
        is_like = serializer.validated_data['is_like']

        reaction, created = Reaction.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id,
            defaults={'is_like': is_like}
        )

        if not created:
            if reaction.is_like == is_like:
                reaction.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            Reaction.objects.filter(pk=reaction.pk).update(is_like=is_like)
            reaction.refresh_from_db()
            updated_serializer = self.get_serializer(reaction)
            return Response(updated_serializer.data, status=status.HTTP_200_OK)

        created_serializer = self.get_serializer(reaction)
        headers = self.get_success_headers(created_serializer.data)
        return Response(created_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # Solo permitimos eliminar reacciones, no actualizarlas directamente por PUT/PATCH
    # La lógica de "cambiar tipo de reacción" se maneja en el `create`
    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) # Método no permitido

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) # Método no permitido
