from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from dashboard.models import EnvironmentalAnalysis
from .models import Report, ReportStatistics
from achievements.service_modules.clerk_achievements import AchievementTracker


def heatmap_view(request):
    """
    Main heatmap page view
    """
    # Map dashboard risk levels to heatmap severity levels
    risk_level_choices = [
        ('low', 'Low'),
        ('high', 'High'), 
        ('critical', 'Critical'),
    ]
    
    # Map dashboard status to heatmap compatible format
    status_choices = [
        ('completed', 'Completed'),
        ('flagged', 'Flagged'),
        ('mixed', 'Mixed'),
        ('unknown', 'Unknown'),
    ]
    
    # Report type mapping for dashboard reports
    report_types = [
        ('pollution', 'Environmental Pollution'),
        ('conservation', 'Wildlife Conservation'),
        ('deforestation', 'Deforestation'),
        ('climate', 'Climate Change'),
        ('other', 'Other'),
    ]
    
    context = {
        'page_title': 'Environmental Heatmap',
        'report_types': report_types,
        'severity_levels': risk_level_choices,
        'status_choices': status_choices,
    }
    return render(request, 'heatmap/heatmap.html', context)


def get_reports_api(request):
    """
    API endpoint to fetch reports for heatmap visualization using dashboard data
    """
    try:
        # Get query parameters for filtering
        report_type = request.GET.get('type', None)
        severity = request.GET.get('severity', None)  # This maps to risk_level in dashboard
        status = request.GET.get('status', None)
        days_back = request.GET.get('days_back', 365)  # Default to 1 year to show all reports
        
        print(f"API Request - Type: {report_type}, Severity: {severity}, Status: {status}, Days: {days_back}")
        
        # Base queryset - Use dashboard EnvironmentalAnalysis model
        queryset = EnvironmentalAnalysis.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        )
        
        # Apply filters
        # Map severity to risk_level since dashboard uses risk_level
        if severity and severity != 'all':
            queryset = queryset.filter(risk_level=severity)
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Date filter
        try:
            days_back = int(days_back)
            if days_back > 0:
                cutoff_date = timezone.now() - timedelta(days=days_back)
                queryset = queryset.filter(created_at__gte=cutoff_date)
        except (ValueError, TypeError):
            pass  # Use default if invalid
        
        # Limit to reasonable number for performance
        queryset = queryset[:1000]
        
        # Convert dashboard reports to heatmap format
        reports_data = []
        for report in queryset:
            # Map dashboard report types to heatmap categories
            report_category = 'other'  # Default category
            title_lower = report.title.lower()
            if any(word in title_lower for word in ['pollut', 'contam', 'toxic', 'chemical']):
                report_category = 'pollution'
            elif any(word in title_lower for word in ['wildlife', 'species', 'animal', 'conservation']):
                report_category = 'conservation'
            elif any(word in title_lower for word in ['forest', 'tree', 'deforest', 'logging']):
                report_category = 'deforestation'
            elif any(word in title_lower for word in ['climate', 'weather', 'temperature', 'warming']):
                report_category = 'climate'
            
            # Skip if filtering by type and doesn't match
            if report_type and report_type != 'all' and report_category != report_type:
                continue
                
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'description': report.description or '',
                'report_type': report_category,
                'report_type_display': report_category.replace('_', ' ').title(),
                'severity': report.risk_level,
                'severity_display': report.get_risk_level_display(),
                'status': report.status,
                'status_display': report.get_status_display(),
                'latitude': float(report.latitude),
                'longitude': float(report.longitude),
                'location_name': report.location,
                'address': report.location,
                'created_at': report.created_at.isoformat(),
                'confidence_score': report.confidence / 100.0,  # Convert percentage to decimal
                'verified': report.status == 'completed',
            })
        
        print(f"API Response - Returning {len(reports_data)} dashboard reports")
        
        response = JsonResponse({
            'success': True,
            'reports': reports_data,
            'count': len(reports_data),
            'filters_applied': {
                'type': report_type,
                'severity': severity,
                'status': status,
                'days_back': days_back
            }
        })
        
        # Add CORS headers for development
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)
        
        response['Access-Control-Allow-Origin'] = '*'
        return response


def get_heatmap_data_api(request):
    """
    API endpoint to get aggregated heatmap data for visualization using dashboard data
    """
    try:
        # Get query parameters
        report_type = request.GET.get('type', None)
        severity = request.GET.get('severity', None)
        days_back = request.GET.get('days_back', 365)  # Default to 1 year to show all reports
        grid_size = float(request.GET.get('grid_size', 0.01))  # Default 0.01 degrees
        
        # Base queryset - Use dashboard EnvironmentalAnalysis model
        # Show all reports regardless of status for comprehensive heatmap view
        queryset = EnvironmentalAnalysis.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        )
        
        # Apply filters
        if severity and severity != 'all':
            queryset = queryset.filter(risk_level=severity)
        
        # Date filter
        try:
            days_back = int(days_back)
            if days_back > 0:
                cutoff_date = timezone.now() - timedelta(days=days_back)
                queryset = queryset.filter(created_at__gte=cutoff_date)
        except (ValueError, TypeError):
            pass
        
        # Group by grid cells and count
        heatmap_data = []
        for report in queryset:
            # Map dashboard report types to heatmap categories
            report_category = 'other'  # Default category
            title_lower = report.title.lower()
            if any(word in title_lower for word in ['pollut', 'contam', 'toxic', 'chemical']):
                report_category = 'pollution'
            elif any(word in title_lower for word in ['wildlife', 'species', 'animal', 'conservation']):
                report_category = 'conservation'
            elif any(word in title_lower for word in ['forest', 'tree', 'deforest', 'logging']):
                report_category = 'deforestation'
            elif any(word in title_lower for word in ['climate', 'weather', 'temperature', 'warming']):
                report_category = 'climate'
            
            # Skip if filtering by type and doesn't match
            if report_type and report_type != 'all' and report_category != report_type:
                continue
            
            # Calculate intensity based on risk level and confidence
            intensity = 1.0
            if report.risk_level == 'critical':
                intensity = 2.0
            elif report.risk_level == 'high':
                intensity = 1.5
            elif report.risk_level == 'low':
                intensity = 0.8
            
            # Adjust intensity based on confidence
            confidence_multiplier = report.confidence / 100.0
            intensity *= confidence_multiplier
            
            heatmap_data.append({
                'lat': float(report.latitude),
                'lng': float(report.longitude),
                'intensity': intensity,
                'report_type': report_category,
                'severity': report.risk_level
            })
        
        return JsonResponse({
            'success': True,
            'heatmap_data': heatmap_data,
            'count': len(heatmap_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_statistics_api(request):
    """
    API endpoint to get report statistics using dashboard data
    """
    try:
        # Use dashboard EnvironmentalAnalysis model
        all_reports = EnvironmentalAnalysis.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        )
        
        # Get basic counts
        total_reports = all_reports.count()
        
        # Status distribution
        status_stats = all_reports.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in status_stats}
        
        # Risk level distribution (mapped to severity)
        severity_stats = all_reports.values('risk_level').annotate(count=Count('id'))
        severity_data = {item['risk_level']: item['count'] for item in severity_stats}
        
        # Generate type distribution by analyzing report titles
        type_data = {
            'pollution': 0,
            'conservation': 0,
            'deforestation': 0,
            'climate': 0,
            'other': 0
        }
        
        for report in all_reports:
            title_lower = report.title.lower()
            if any(word in title_lower for word in ['pollut', 'contam', 'toxic', 'chemical']):
                type_data['pollution'] += 1
            elif any(word in title_lower for word in ['wildlife', 'species', 'animal', 'conservation']):
                type_data['conservation'] += 1
            elif any(word in title_lower for word in ['forest', 'tree', 'deforest', 'logging']):
                type_data['deforestation'] += 1
            elif any(word in title_lower for word in ['climate', 'weather', 'temperature', 'warming']):
                type_data['climate'] += 1
            else:
                type_data['other'] += 1
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_reports = all_reports.filter(created_at__gte=week_ago).count()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_reports': total_reports,
                'recent_reports': recent_reports,
                'status_distribution': status_data,
                'type_distribution': type_data,
                'severity_distribution': severity_data,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_report_api(request):
    """
    API endpoint to create a new environmental report in dashboard model
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'description', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Map heatmap severity to dashboard risk level
        severity = data.get('severity', 'low')
        risk_level_mapping = {
            'low': 'low',
            'medium': 'high',
            'high': 'high', 
            'critical': 'critical'
        }
        risk_level = risk_level_mapping.get(severity, 'low')
        
        # Determine status based on severity
        status = 'completed'
        if risk_level == 'critical':
            status = 'flagged'
        elif risk_level == 'high' and data.get('confidence_score', 0.5) < 0.7:
            status = 'mixed'
        
        # Create new report in dashboard model
        report = EnvironmentalAnalysis.objects.create(
            title=data['title'],
            description=data['description'],
            location=data.get('location_name', f"{data['latitude']}, {data['longitude']}"),
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            risk_level=risk_level,
            status=status,
            confidence=int(data.get('confidence_score', 0.7) * 100),  # Convert to percentage
            created_by=request.user if request.user.is_authenticated else None,
        )
        
        # Convert to heatmap format for response
        response_data = {
            'id': report.id,
            'title': report.title,
            'description': report.description or '',
            'report_type': 'other',  # Default since we don't store this explicitly
            'severity': report.risk_level,
            'status': report.status,
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
            'location_name': report.location,
            'created_at': report.created_at.isoformat(),
            'confidence_score': report.confidence / 100.0,
            'verified': report.status == 'completed',
        }
        
        return JsonResponse({
            'success': True,
            'report': response_data,
            'message': 'Report created successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
