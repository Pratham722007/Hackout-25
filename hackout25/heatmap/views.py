from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import Report, ReportStatistics


def heatmap_view(request):
    """
    Main heatmap page view
    """
    context = {
        'page_title': 'Environmental Heatmap',
        'report_types': Report.REPORT_TYPES,
        'severity_levels': Report.SEVERITY_CHOICES,
        'status_choices': Report.STATUS_CHOICES,
    }
    return render(request, 'heatmap/heatmap.html', context)


def get_reports_api(request):
    """
    API endpoint to fetch reports for heatmap visualization
    """
    try:
        # Get query parameters for filtering
        report_type = request.GET.get('type', None)
        severity = request.GET.get('severity', None)
        status = request.GET.get('status', None)
        days_back = request.GET.get('days_back', 30)
        
        # Base queryset
        queryset = Report.objects.all()
        
        # Apply filters
        if report_type and report_type != 'all':
            queryset = queryset.filter(report_type=report_type)
        
        if severity and severity != 'all':
            queryset = queryset.filter(severity=severity)
        
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
        
        # Convert to list of dictionaries
        reports_data = [report.to_dict() for report in queryset]
        
        return JsonResponse({
            'success': True,
            'reports': reports_data,
            'count': len(reports_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_heatmap_data_api(request):
    """
    API endpoint to get aggregated heatmap data for visualization
    """
    try:
        # Get query parameters
        report_type = request.GET.get('type', None)
        severity = request.GET.get('severity', None)
        days_back = request.GET.get('days_back', 30)
        grid_size = float(request.GET.get('grid_size', 0.01))  # Default 0.01 degrees
        
        # Base queryset
        queryset = Report.objects.filter(status='validated')
        
        # Apply filters
        if report_type and report_type != 'all':
            queryset = queryset.filter(report_type=report_type)
        
        if severity and severity != 'all':
            queryset = queryset.filter(severity=severity)
        
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
            # Round coordinates to grid
            grid_lat = round(float(report.latitude) / grid_size) * grid_size
            grid_lng = round(float(report.longitude) / grid_size) * grid_size
            
            heatmap_data.append({
                'lat': float(report.latitude),
                'lng': float(report.longitude),
                'intensity': 1.0,  # Can be adjusted based on severity
                'report_type': report.report_type,
                'severity': report.severity
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
    API endpoint to get report statistics
    """
    try:
        # Get basic counts
        total_reports = Report.objects.count()
        
        # Status distribution
        status_stats = Report.objects.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in status_stats}
        
        # Type distribution
        type_stats = Report.objects.values('report_type').annotate(count=Count('id'))
        type_data = {item['report_type']: item['count'] for item in type_stats}
        
        # Severity distribution
        severity_stats = Report.objects.values('severity').annotate(count=Count('id'))
        severity_data = {item['severity']: item['count'] for item in severity_stats}
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_reports = Report.objects.filter(created_at__gte=week_ago).count()
        
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
    API endpoint to create a new environmental report
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'description', 'report_type', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Create new report
        report = Report.objects.create(
            title=data['title'],
            description=data['description'],
            report_type=data['report_type'],
            severity=data.get('severity', 'medium'),
            latitude=data['latitude'],
            longitude=data['longitude'],
            location_name=data.get('location_name', ''),
            address=data.get('address', ''),
            reporter_name=data.get('reporter_name', ''),
            reporter_email=data.get('reporter_email', ''),
            reporter_phone=data.get('reporter_phone', ''),
        )
        
        return JsonResponse({
            'success': True,
            'report': report.to_dict(),
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
