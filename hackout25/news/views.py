from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import F, Q
from django.views.decorators.http import require_POST

from .models import Article

def news_home(request):
    from django.core.cache import cache
    
    q = request.GET.get('q', '')
    team = request.GET.get('team', '')
    from_date = request.GET.get('from')  
    to_date = request.GET.get('to')
    
    # Create cache key based on filters
    cache_key = f"news_home_{q}_{team}_{from_date}_{to_date}"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Base queryset with optimized filtering
        articles = Article.objects.filter(
            category__iexact="forest"
        ).exclude(
            Q(image_url__isnull=True) | Q(image_url__exact='')
        ).select_related()  # Optimize related queries

        # Apply filters
        if q:
            articles = articles.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if team:
            articles = articles.filter(teams__name__iexact=team)
        if from_date and to_date:
            articles = articles.filter(published__date__range=[from_date, to_date])

        # Get trending and latest with single queries
        trending = list(articles.order_by('-likes')[:10])
        latest = list(articles.order_by('-published')[:20])

        # Unique team names (excluding blanks/nulls) - optimized query
        teams = set(articles.exclude(
            Q(teams__name__isnull=True) | Q(teams__name='')
        ).values_list('teams__name', flat=True).distinct())
        
        cached_data = {
            'trending': trending,
            'latest': latest,
            'teams': teams
        }
        
        # Cache for 5 minutes if no search query, 1 minute if search query
        cache_timeout = 60 if q or team or from_date or to_date else 300
        cache.set(cache_key, cached_data, cache_timeout)
    
    trending = cached_data['trending']
    latest = cached_data['latest']
    teams = cached_data['teams']

    context = {
        'trending': trending,
        'latest': latest,
        'teams': teams,
        'query': q
    }

    return render(request, 'news/home.html', context)


def latest_articles_json(request):
    from django.core.cache import cache
    
    # Try to get data from cache first
    cache_key = 'latest_articles_json'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Get articles with optimized query
        articles = Article.objects.filter(
            category__iexact="forest"
        ).exclude(
            Q(image_url__isnull=True) | Q(image_url__exact='')
        ).order_by('-published')[:10]

        cached_data = [
            {
                'id': art.id,
                'title': art.title,
                'description': art.description,
                'image_url': art.image_url,
                'link': art.link,
                'likes': art.likes,
                'published': art.published.strftime('%b %d, %Y'),
            }
            for art in articles
        ]
        
        # Cache for 2 minutes
        cache.set(cache_key, cached_data, 120)
    
    return JsonResponse({'articles': cached_data})

@require_POST
def like_article(request, aid):
    article = get_object_or_404(Article, id=aid)
    article.likes = F('likes') + 1
    article.save(update_fields=['likes'])
    article.refresh_from_db()
    return JsonResponse({'likes': article.likes})
