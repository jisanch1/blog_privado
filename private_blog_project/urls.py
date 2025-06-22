"""
URL configuration for private_blog_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# private_blog_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from blog import views as blog_views # Importa las vistas de tu app 'blog'
from rest_framework.authtoken.views import obtain_auth_token # Para la autenticación por token

# Crea un router para tus ViewSets
router = DefaultRouter()
router.register(r'posts', blog_views.PostViewSet)
router.register(r'comments', blog_views.CommentViewSet)
router.register(r'reactions', blog_views.ReactionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # Incluye las URLs generadas por el router de DRF
    path('api-auth/', include('rest_framework.urls')), # Opcional: URLs para el login/logout en el navegador de DRF
    path('api/token-auth/', obtain_auth_token), # Endpoint para obtener un token de autenticación
]
