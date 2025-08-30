from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User


class Report(models.Model):
    """
    Environmental report model for heatmap visualization
    """
    
    REPORT_TYPES = [
        ('air_pollution', 'Air Pollution'),
        ('water_pollution', 'Water Pollution'),
        ('noise_pollution', 'Noise Pollution'),
        ('waste_management', 'Waste Management'),
        ('deforestation', 'Deforestation'),
        ('wildlife_conservation', 'Wildlife Conservation'),
        ('climate_change', 'Climate Change'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('validated', 'Validated'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Location Information
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Additional Data
    reporter_name = models.CharField(max_length=100, blank=True, null=True)
    reporter_email = models.EmailField(blank=True, null=True)
    reporter_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for analysis
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence score (0-1)")
    verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    
    # User tracking for achievements
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_reports')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_reports')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['report_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()}) - {self.location_name or 'Unknown Location'}"
    
    def to_dict(self):
        """Convert model instance to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'report_type_display': self.get_report_type_display(),
            'severity': self.severity,
            'severity_display': self.get_severity_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'location_name': self.location_name,
            'address': self.address,
            'reporter_name': self.reporter_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'confidence_score': self.confidence_score,
            'verified': self.verified,
        }


class ReportStatistics(models.Model):
    """
    Model to store pre-calculated statistics for performance optimization
    """
    date = models.DateField(auto_now_add=True)
    total_reports = models.IntegerField(default=0)
    pending_reports = models.IntegerField(default=0)
    validated_reports = models.IntegerField(default=0)
    rejected_reports = models.IntegerField(default=0)
    
    # Type distribution
    air_pollution_count = models.IntegerField(default=0)
    water_pollution_count = models.IntegerField(default=0)
    noise_pollution_count = models.IntegerField(default=0)
    waste_management_count = models.IntegerField(default=0)
    deforestation_count = models.IntegerField(default=0)
    wildlife_conservation_count = models.IntegerField(default=0)
    climate_change_count = models.IntegerField(default=0)
    other_count = models.IntegerField(default=0)
    
    # Severity distribution
    low_severity_count = models.IntegerField(default=0)
    medium_severity_count = models.IntegerField(default=0)
    high_severity_count = models.IntegerField(default=0)
    critical_severity_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Statistics for {self.date} - {self.total_reports} reports"
