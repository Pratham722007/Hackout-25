from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import EnvironmentalAnalysis
from .forms import EnvironmentalAnalysisForm
from .ai_model import environmental_analyzer
import re
import os

def dashboard_view(request):
    analyses = EnvironmentalAnalysis.objects.all()[:10]  # Recent 10 analyses
    stats = EnvironmentalAnalysis.get_stats()
    
    # Risk distribution for pie chart
    risk_distribution = {
        'critical': EnvironmentalAnalysis.objects.filter(risk_level='critical').count(),
        'high': EnvironmentalAnalysis.objects.filter(risk_level='high').count(),
        'low': EnvironmentalAnalysis.objects.filter(risk_level='low').count(),
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
    score = 50  # Base score
    
    # Increase confidence for specific locations
    if any(word in location.lower() for word in ['amazon', 'forest', 'national park', 'reserve']):
        score += 30
    elif location.strip():
        score += 20
    
    # Increase confidence for detailed titles
    if len(title) > 30:
        score += 20
    elif len(title) > 15:
        score += 10
    
    return min(score, 100)  # Cap at 100
