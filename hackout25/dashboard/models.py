from django.db import models
from django.utils import timezone

class EnvironmentalAnalysis(models.Model):
    RISK_CHOICES = [
        ('low', 'Low'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('flagged', 'Flagged'),
        ('mixed', 'Mixed'),
        ('unknown', 'Unknown'),
    ]
    
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude coordinate of the location")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude coordinate of the location")
    description = models.TextField(blank=True, help_text="Additional details about the environmental report")
    image = models.ImageField(upload_to='environmental_images/', null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='low')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
    confidence = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @classmethod
    def get_stats(cls):
        total = cls.objects.count()
        completed = cls.objects.filter(status='completed').count()
        flagged = cls.objects.filter(status='flagged').count()
        avg_confidence = cls.objects.aggregate(models.Avg('confidence'))['confidence__avg'] or 0
        
        return {
            'total': total,
            'completed': completed,
            'flagged': flagged,
            'avg_confidence': int(avg_confidence)
        }
