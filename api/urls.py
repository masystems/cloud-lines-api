from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.SimpleRouter()
#router.register('', views.test.as_view(), basename='test')

urlpatterns = [
    #path('', views.dash, name='dash'),
    path('', include(router.urls)),
    path('test', views.test, name="instances"),
]