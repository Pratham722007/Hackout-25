from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

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
    
    # User tracking for achievements
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_analyses')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_analyses')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['status']),
            models.Index(fields=['risk_level', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    @classmethod
    def get_stats(cls):
        from django.core.cache import cache
        from django.db.models import Count, Q, Avg
        
        # Try to get stats from cache first
        cache_key = 'environmental_stats'
        stats = cache.get(cache_key)
        
        if stats is None:
            # Calculate stats with optimized queries
            stats_data = cls.objects.aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                flagged=Count('id', filter=Q(status='flagged')),
                avg_confidence=Avg('confidence')
            )
            
            stats = {
                'total': stats_data['total'] or 0,
                'completed': stats_data['completed'] or 0,
                'flagged': stats_data['flagged'] or 0,
                'avg_confidence': int(stats_data['avg_confidence'] or 0)
            }
            
            # Cache for 2 minutes
            cache.set(cache_key, stats, 120)
        
        return stats


class Alert(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low - Information Only'),
        ('medium', 'Medium - Attention Required'),
        ('high', 'High - Urgent Action Needed'),
        ('critical', 'Critical - Immediate Response Required'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='alert_images/', null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_alerts')
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipients_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"
    
    @property
    def priority_color(self):
        colors = {
            'low': '#27ae60',
            'medium': '#f39c12', 
            'high': '#e67e22',
            'critical': '#e74c3c'
        }
        return colors.get(self.priority, '#3498db')
    
    @property
    def priority_icon(self):
        icons = {
            'low': 'info-circle',
            'medium': 'exclamation-triangle',
            'high': 'exclamation-triangle',
            'critical': 'exclamation-circle'
        }
        return icons.get(self.priority, 'bell')


class AlertRecipient(models.Model):
    """Track which users received specific alerts"""
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['alert', 'user']
        indexes = [
            models.Index(fields=['alert', 'user']),
        ]
    
    def __str__(self):
        return f"{self.alert.title} -> {self.user.email}"
