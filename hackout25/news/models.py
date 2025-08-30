from django.db import models

# Create your models here.

class Article( models.Model ):
    title = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    link = models.URLField(unique=True)
    image_url = models.URLField(null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    published = models.DateTimeField(null=True, blank=True)
    likes = models.IntegerField(default=0)
    teams = models.ManyToManyField('Team', blank=True)  # optional, for filtering
    category = models.CharField(max_length=100, default="cricket")
    # ... any other fields
    def __str__(self): return self.title


class Team(models.Model):
    name = models.CharField(max_length=100)
    # add other fields as needed