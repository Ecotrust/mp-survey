from django.db import models

# Create your models here.
class MapGroup(models.Model):
    """Represents a group of users imported from MARCO Portal that can be assigned to a survey."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name