from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('tasks', views.Tasks, basename='tasks')
router.register('reports', views.Reports, basename='reports')
router.register('custom_fields', views.CustomFields, basename='custom_fields')

urlpatterns = router.urls
