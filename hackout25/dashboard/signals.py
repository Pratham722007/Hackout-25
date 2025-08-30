from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import EnvironmentalAnalysis
from news.models import Article


@receiver([post_save, post_delete], sender=EnvironmentalAnalysis)
def clear_environmental_cache(sender, **kwargs):
    """Clear cached environmental analysis data when data changes"""
    cache.delete('environmental_stats')


@receiver([post_save, post_delete], sender=Article)
def clear_news_cache(sender, **kwargs):
    """Clear cached news data when articles change"""
    cache.delete('latest_articles_json')
    # Clear all news home cache entries (pattern-based would be better in production)
    cache.clear()  # Simple approach - clears all cache
