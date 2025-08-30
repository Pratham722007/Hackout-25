#!/usr/bin/env python
"""
Performance warmup script to preload cache with commonly accessed data
Run this after deployment or during maintenance windows
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from django.core.cache import cache
from dashboard.models import EnvironmentalAnalysis
from news.models import Article
from news.views import latest_articles_json
from django.test import RequestFactory


def warm_dashboard_cache():
    """Preload dashboard statistics cache"""
    print("Warming up dashboard cache...")
    
    # Load stats into cache
    stats = EnvironmentalAnalysis.get_stats()
    print(f"Loaded dashboard stats: {stats}")
    
    # Load recent analyses
    analyses = list(EnvironmentalAnalysis.objects.select_related().order_by('-created_at')[:10])
    print(f"Loaded {len(analyses)} recent analyses")


def warm_news_cache():
    """Preload news cache"""
    print("Warming up news cache...")
    
    try:
        # Use RequestFactory to simulate request for news API
        factory = RequestFactory()
        request = factory.get('/news/latest-json/')
        
        # This will populate the cache
        from news.views import latest_articles_json
        response = latest_articles_json(request)
        print("Loaded latest articles JSON cache")
        
        # Load main news page cache (without filters)
        from news.views import news_home
        request = factory.get('/news/')
        response = news_home(request)
        print("Loaded news home page cache")
        
    except Exception as e:
        print(f"Error warming news cache: {e}")


def warm_ai_model():
    """Warm up AI model (trigger lazy loading)"""
    print("Warming up AI model...")
    
    try:
        from dashboard.ai_model import environmental_analyzer
        # This will trigger model loading if not already loaded
        environmental_analyzer._ensure_model_loaded()
        
        if environmental_analyzer._model_loaded:
            print("AI model loaded successfully")
        else:
            print("AI model failed to load (will use fallback)")
            
    except Exception as e:
        print(f"Error warming AI model: {e}")


def main():
    """Main warmup routine"""
    print("Starting performance warmup...")
    
    # Clear existing cache first
    cache.clear()
    print("Cleared existing cache")
    
    # Warm up different components
    warm_dashboard_cache()
    warm_news_cache()
    warm_ai_model()
    
    print("Performance warmup complete!")
    
    # Show cache stats
    print("\nCache keys after warmup:")
    try:
        # This won't work with LocMemCache, but useful for other cache backends
        print("Cache backend:", cache.__class__.__name__)
    except:
        pass


if __name__ == '__main__':
    main()
