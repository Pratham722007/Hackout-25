from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .models import EnvironmentalAnalysis, Alert
from .forms import EnvironmentalAnalysisForm
from .ai_model import environmental_analyzer
from .geocoding import geocoding_service
from .services.email_service import AlertEmailService
import re
import os
import json
import threading

def dashboard_view(request):
    from django.db.models import Count, Q
    
    # Get recent analyses with single query
    analyses = EnvironmentalAnalysis.objects.select_related().order_by('-created_at')[:10]
    
    # Get stats with optimized queries
    stats = EnvironmentalAnalysis.get_stats()
    
    # Risk distribution for pie chart - single query with aggregation
    risk_distribution_data = EnvironmentalAnalysis.objects.aggregate(
        critical=Count('id', filter=Q(risk_level='critical')),
        high=Count('id', filter=Q(risk_level='high')),
        low=Count('id', filter=Q(risk_level='low'))
    )
    risk_distribution = {
        'critical': risk_distribution_data['critical'],
        'high': risk_distribution_data['high'],
        'low': risk_distribution_data['low'],
    }
    
    context = {
        'analyses': analyses,
        'stats': stats,
        'risk_distribution': risk_distribution,
    }
    return render(request, 'dashboard/dashboard.html', context)

def new_analysis_view(request):
    if request.method == 'POST':
        form = EnvironmentalAnalysisForm(request.POST, request.FILES)
        if form.is_valid():
            analysis = form.save(commit=False)
            
            # Get coordinates from POST data if available
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude and longitude:
                try:
                    analysis.latitude = float(latitude)
                    analysis.longitude = float(longitude)
                except ValueError:
                    # If coordinates are invalid, try to get them from location
                    coord_result = geocoding_service.get_coordinates(analysis.location)
                    if coord_result:
                        analysis.latitude = coord_result['latitude']
                        analysis.longitude = coord_result['longitude']
            
            # Use AI model for image analysis if image is provided
            if analysis.image:
                try:
                    # Get the full path to the uploaded image
                    image_path = analysis.image.path
                    
                    # Use AI model to analyze the image
                    ai_result = environmental_analyzer.detect_environmental_content(image_path)
                    
                    # Update analysis based on AI results
                    analysis.risk_level = ai_result['risk_level']
                    analysis.confidence = ai_result['confidence']
                    
                    # Determine status based on AI analysis
                    if not ai_result['is_environmental']:
                        analysis.status = 'unknown'
                    elif ai_result['risk_level'] == 'critical':
                        analysis.status = 'flagged'
                    elif ai_result['confidence'] < 50:
                        analysis.status = 'mixed'
                    else:
                        analysis.status = 'completed'
                        
                except Exception as e:
                    print(f"AI analysis failed: {e}")
                    # Fallback to keyword-based analysis
                    analysis.risk_level = determine_risk_level(analysis.title, analysis.location)
                    analysis.status = determine_status(analysis.title, analysis.location)
                    analysis.confidence = calculate_confidence(analysis.title, analysis.location)
            else:
                # No image provided, use keyword-based analysis
                analysis.risk_level = determine_risk_level(analysis.title, analysis.location)
                analysis.status = determine_status(analysis.title, analysis.location)
                analysis.confidence = calculate_confidence(analysis.title, analysis.location)
            
            analysis.save()
            
            # Automatically create alert for high risk or critical reports
            if analysis.risk_level in ['high', 'critical']:
                try:
                    # Get or create system user for auto-generated alerts
                    system_user, created = User.objects.get_or_create(
                        username='system_auto',
                        defaults={
                            'email': 'system@ecovalidate.com',
                            'first_name': 'System',
                            'last_name': 'Auto-Alert'
                        }
                    )
                    
                    # Determine alert priority based on risk level
                    alert_priority = 'critical' if analysis.risk_level == 'critical' else 'high'
                    
                    # Create alert with report details
                    alert_title = f"🚨 {analysis.risk_level.upper()} RISK: {analysis.title}"
                    alert_description = f"""
AUTO-GENERATED ALERT FROM NEW ENVIRONMENTAL REPORT

📍 Location: {analysis.location}
🎯 Risk Level: {analysis.risk_level.upper()}
📊 AI Confidence: {analysis.confidence}%
📅 Reported: {analysis.created_at.strftime('%Y-%m-%d %H:%M UTC')}

📝 Description:
{analysis.description if analysis.description else 'No additional description provided.'}

⚠️ This alert was automatically generated based on AI analysis of a new environmental report. Immediate attention may be required.
                    """
                    
                    # Create the alert
                    alert = Alert.objects.create(
                        title=alert_title,
                        description=alert_description,
                        location=analysis.location,
                        priority=alert_priority,
                        image=analysis.image,
                        created_by=system_user
                    )
                    
                    # Send alert emails in background
                    def send_auto_alert_emails():
                        try:
                            success_count, total_count = AlertEmailService.send_alert_to_all_users(alert)
                            print(f"Auto-alert sent to {success_count}/{total_count} users for report: {analysis.title}")
                        except Exception as e:
                            print(f"Error sending auto-alert emails: {e}")
                    
                    # Start email sending in background
                    email_thread = threading.Thread(target=send_auto_alert_emails)
                    email_thread.daemon = True
                    email_thread.start()
                    
                    print(f"Auto-generated alert created for {analysis.risk_level} risk report: {analysis.title}")
                    
                except Exception as e:
                    print(f"Error creating auto-alert for report {analysis.title}: {e}")
            
            return redirect('dashboard')
    else:
        form = EnvironmentalAnalysisForm()
    
    return render(request, 'dashboard/new_analysis.html', {'form': form})

def determine_risk_level(title, location):
    """Simple AI logic to determine risk level based on keywords"""
    title_lower = title.lower()
    location_lower = location.lower()
    
    # Keywords that indicate critical risk
    critical_keywords = [
        'mangrove', 'deforestation', 'oil spill', 'pollution', 'toxic',
        'endangered', 'extinction', 'illegal', 'mining', 'dumping'
    ]
    
    # Keywords that indicate high risk
    high_keywords = [
        'erosion', 'flood', 'drought', 'wildfire', 'overfishing',
        'coral', 'bleaching', 'habitat loss'
    ]
    
    # Check for critical risk
    if any(keyword in title_lower or keyword in location_lower for keyword in critical_keywords):
        return 'critical'
    
    # Check for high risk
    if any(keyword in title_lower or keyword in location_lower for keyword in high_keywords):
        return 'high'
    
    # Default to low risk
    return 'low'

def determine_status(title, location):
    """Determine analysis status"""
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['mixed', 'partial', 'unclear']):
        return 'mixed'
    elif any(word in title_lower for word in ['unknown', 'unidentified', 'unclear']):
        return 'unknown'
    elif any(word in title_lower for word in ['flag', 'alert', 'warning']):
        return 'flagged'
    
    return 'completed'

def calculate_confidence(title, location):
    """Calculate confidence score based on specificity of information"""
    score = 60  # Increased base score from 50 to 60
    
    # Increase confidence for specific locations
    if any(word in location.lower() for word in ['amazon', 'forest', 'national park', 'reserve', 'ocean', 'river', 'mountain']):
        score += 25
    elif location.strip():
        score += 15
    
    # Increase confidence for detailed titles
    if len(title) > 30:
        score += 15
    elif len(title) > 15:
        score += 10
    
    # Boost confidence for environmental keywords in title
    environmental_keywords = ['pollution', 'deforestation', 'wildlife', 'ecosystem', 'conservation', 
                            'climate', 'biodiversity', 'endangered', 'habitat', 'sustainable']
    if any(keyword in title.lower() for keyword in environmental_keywords):
        score += 10
    
    return min(score, 95)  # Cap at 95 instead of 100 for realism

def get_coordinates(request):
    """AJAX view to get coordinates for a location"""
    if request.method == 'GET':
        location = request.GET.get('location', '').strip()
        
        if not location:
            return JsonResponse({
                'success': False,
                'error': 'Location parameter is required'
            })
        
        try:
            # Get coordinates from geocoding service
            result = geocoding_service.get_coordinates(location)
            
            if result:
                return JsonResponse({
                    'success': True,
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'display_name': result['display_name'],
                    'coordinates_text': f"{result['latitude']:.6f}, {result['longitude']:.6f}"
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Location not found. Please check the spelling or try a more specific location.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error retrieving coordinates: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


def send_alert_view(request):
    """Handle sending environmental alerts to all users"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            location = request.POST.get('location', '').strip()
            priority = request.POST.get('priority', 'medium')
            image = request.FILES.get('image')
            
            # Validate required fields
            if not title or not description:
                return JsonResponse({
                    'success': False,
                    'message': 'Title and description are required'
                })
            
            if priority not in ['low', 'medium', 'high', 'critical']:
                priority = 'medium'
            
            # Create a default user if no authentication system is in place
            # In a real system, you'd use request.user
            try:
                created_by = request.user if request.user.is_authenticated else User.objects.first()
                if not created_by:
                    # Create a default system user if no users exist
                    created_by = User.objects.create_user(
                        username='system',
                        email='system@ecovalidate.com',
                        first_name='System',
                        last_name='Alert'
                    )
            except:
                created_by = User.objects.first()
            
            # Create the alert
            alert = Alert.objects.create(
                title=title,
                description=description,
                location=location,
                priority=priority,
                image=image,
                created_by=created_by
            )
            
            # Send emails in a separate thread to avoid blocking the response
            def send_emails():
                try:
                    success_count, total_count = AlertEmailService.send_alert_to_all_users(alert)
                    print(f"Alert sent to {success_count}/{total_count} users")
                except Exception as e:
                    print(f"Error sending alert emails: {e}")
            
            # Start email sending in background
            email_thread = threading.Thread(target=send_emails)
            email_thread.daemon = True
            email_thread.start()
            
            return JsonResponse({
                'success': True,
                'message': f'Alert created successfully! Emails are being sent to all registered users.',
                'alert_id': alert.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating alert: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def reports_view(request):
    """Display all environmental analysis reports with pagination and filtering"""
    # Get filter parameters
    risk_filter = request.GET.get('risk', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Start with all reports
    reports = EnvironmentalAnalysis.objects.all().order_by('-created_at')
    
    # Apply filters
    if risk_filter and risk_filter in ['low', 'high', 'critical']:
        reports = reports.filter(risk_level=risk_filter)
    
    if status_filter and status_filter in ['completed', 'flagged', 'mixed', 'unknown']:
        reports = reports.filter(status=status_filter)
    
    if search_query:
        reports = reports.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reports, 12)  # Show 12 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    stats = {
        'total': reports.count(),
        'critical': reports.filter(risk_level='critical').count(),
        'high': reports.filter(risk_level='high').count(),
        'low': reports.filter(risk_level='low').count(),
        'completed': reports.filter(status='completed').count(),
        'flagged': reports.filter(status='flagged').count(),
    }
    
    context = {
        'reports': page_obj,
        'stats': stats,
        'risk_filter': risk_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'risk_choices': EnvironmentalAnalysis.RISK_CHOICES,
        'status_choices': EnvironmentalAnalysis.STATUS_CHOICES,
    }
    
    return render(request, 'dashboard/reports.html', context)

def report_detail_view(request, report_id):
    """Display detailed view of a specific environmental analysis report"""
    report = get_object_or_404(EnvironmentalAnalysis, id=report_id)
    
    context = {
        'report': report,
    }
    
    return render(request, 'dashboard/report_detail.html', context)
