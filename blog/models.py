# blog/models.py

from django.db import models
from django.contrib.auth.models import User # Importamos el modelo de usuario de Django
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation  # Importa GenericForeignKey
from django.contrib.contenttypes.models import ContentType  # ¡Importa ContentType desde aquí!


# Modelo para las publicaciones del blog
class Post(models.Model):
    title = models.CharField(max_length=200) # Título de la publicación
    content = models.TextField() # Contenido del blog
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts') # Relación con el autor (tú)
    created_at = models.DateTimeField(auto_now_add=True) # Fecha y hora de creación (automático)
    updated_at = models.DateTimeField(auto_now=True) # Fecha y hora de última actualización (automático)
    reactions = GenericRelation('Reaction')

    class Meta:
        ordering = ['-created_at'] # Ordenar los posts por fecha de creación descendente

    def __str__(self):
        return self.title # Representación legible del objeto

# Modelo para los comentarios
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments') # Relación con la publicación a la que pertenece
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments') # Relación con el autor del comentario
    content = models.TextField() # Contenido del comentario
    created_at = models.DateTimeField(auto_now_add=True) # Fecha y hora de creación (automático)
    reactions = GenericRelation('Reaction')

    class Meta:
        ordering = ['created_at'] # Ordenar los comentarios por fecha de creación ascendente

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}' # Representación legible

# Modelo para las reacciones (Me Gusta/No Me Gusta)
class Reaction(models.Model):
    # Campo para el objeto al que se le da "like" o "dislike"
    # Usamos ContentType y GenericForeignKey para poder aplicar reacciones a Posts O Comments
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions') # Usuario que reacciona

    # Tipo de reacción: True para "Me Gusta", False para "No Me Gusta"
    is_like = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Asegura que un usuario solo pueda reaccionar una vez a un objeto específico
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'user'],
                name='unique_reaction'
            )
        ]

        # Optimiza consultas y borrados filtrando por el objeto relacionado
        indexes = [
            models.Index(fields=['content_type', 'object_id'])
        ]

    def __str__(self):
        reaction_type = "Like" if self.is_like else "Dislike"
        return f'{self.user.username} {reaction_type}d {self.content_object}'
    