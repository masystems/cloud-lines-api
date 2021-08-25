from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('tasks', views.Tasks, basename='tasks')

urlpatterns = router.urls
