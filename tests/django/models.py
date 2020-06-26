from django.db import models


class DummyModel(models.Model):
    text = models.CharField(max_length=32)
    extra = models.CharField(null=True, blank=True, max_length=64)
