from django.db import models


class ExportQueue(models.Model):
    created = models.DateTimeField()
    domain = models.CharField(max_length=255)
