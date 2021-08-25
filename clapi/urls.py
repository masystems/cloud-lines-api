from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('api/', include('api.urls')),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
    path('admin/', admin.site.urls),
]
