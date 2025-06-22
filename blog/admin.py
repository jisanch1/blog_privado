from django.contrib import admin
from .models import Post, Comment, Reaction

# Registra tus modelos para que aparezcan en el panel de administración
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Reaction)
