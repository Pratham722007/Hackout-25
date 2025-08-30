from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
    
    def __str__(self):
        return f"{self.alert.title} -> {self.user.email}"
