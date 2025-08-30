from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Achievement, UserAchievement, UserStats, AchievementNotification, Leaderboard
from .services import AchievementService

def achievements_dashboard(request):
    """Main achievements dashboard"""
    try:
        progress_summary = AchievementService.get_user_progress_summary(request.user)
        
        # Get achievements by category
        categories = Achievement.CATEGORY_CHOICES
        achievements_by_category = {}
        
        for category_key, category_name in categories:
            user_achievements = UserAchievement.objects.filter(
                user=request.user,
                achievement__category=category_key,
                achievement__is_active=True
            ).select_related('achievement').order_by('achievement__tier', 'achievement__target_value')
            
            achievements_by_category[category_key] = {
                'name': category_name,
                'achievements': user_achievements
            }
        
        # Get recent notifications
        recent_notifications = AchievementService.get_unread_notifications(request.user)[:5]
        
        context = {
            'progress_summary': progress_summary,
            'achievements_by_category': achievements_by_category,
            'recent_notifications': recent_notifications,
            'page_title': 'Achievements Dashboard'
        }
        
        return render(request, 'achievements/dashboard.html', context)
        
    except Exception as e:
        return render(request, 'achievements/dashboard.html', {
            'error': str(e),
            'page_title': 'Achievements Error'
        })


@login_required
def achievement_detail(request, achievement_id):
    """Detail view for a specific achievement"""
    achievement = get_object_or_404(Achievement, id=achievement_id, is_active=True)
    
    try:
        user_achievement = UserAchievement.objects.get(
            user=request.user,
            achievement=achievement
        )
    except UserAchievement.DoesNotExist:
        # Create if doesn't exist
        user_achievement = UserAchievement.objects.create(
            user=request.user,
            achievement=achievement,
            current_progress=0
        )
    
    # Get recent users who unlocked this achievement
    recent_unlocks = UserAchievement.objects.filter(
        achievement=achievement,
        is_unlocked=True
    ).select_related('user').order_by('-unlocked_at')[:10]
    
    # Calculate completion stats
    total_users = UserAchievement.objects.filter(achievement=achievement).count()
    unlocked_users = UserAchievement.objects.filter(
        achievement=achievement,
        is_unlocked=True
    ).count()
    
    completion_rate = (unlocked_users / total_users * 100) if total_users > 0 else 0
    
    context = {
        'achievement': achievement,
        'user_achievement': user_achievement,
        'recent_unlocks': recent_unlocks,
        'completion_rate': round(completion_rate, 1),
        'total_users': total_users,
        'unlocked_users': unlocked_users,
        'page_title': f'Achievement: {achievement.name}'
    }
    
    return render(request, 'achievements/detail.html', context)


@login_required
def leaderboard(request):
    """Leaderboard page"""
    leaderboard_type = request.GET.get('type', 'points')
    period = request.GET.get('period', 'all')  # all, month, week
    
    # Calculate date range
    now = timezone.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = None
    
    # Get leaderboard data
    if leaderboard_type == 'points':
        query = UserStats.objects.all().order_by('-total_points')
    elif leaderboard_type == 'reports':
        query = UserStats.objects.all().order_by('-reports_created')
    elif leaderboard_type == 'validations':
        query = UserStats.objects.all().order_by('-reports_validated')
    elif leaderboard_type == 'streak':
        query = UserStats.objects.all().order_by('-streak_best')
    elif leaderboard_type == 'achievements':
        query = UserStats.objects.all().order_by('-achievements_unlocked')
    else:
        query = UserStats.objects.all().order_by('-total_points')
    
    # Apply date filtering if needed
    if start_date and leaderboard_type in ['points', 'reports', 'validations']:
        # This would require additional filtering logic based on timestamps
        pass
    
    # Paginate results
    paginator = Paginator(query, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's position
    try:
        user_stats = UserStats.objects.get(user=request.user)
        if leaderboard_type == 'points':
            user_rank = UserStats.objects.filter(total_points__gt=user_stats.total_points).count() + 1
            user_score = user_stats.total_points
        elif leaderboard_type == 'reports':
            user_rank = UserStats.objects.filter(reports_created__gt=user_stats.reports_created).count() + 1
            user_score = user_stats.reports_created
        elif leaderboard_type == 'validations':
            user_rank = UserStats.objects.filter(reports_validated__gt=user_stats.reports_validated).count() + 1
            user_score = user_stats.reports_validated
        elif leaderboard_type == 'streak':
            user_rank = UserStats.objects.filter(streak_best__gt=user_stats.streak_best).count() + 1
            user_score = user_stats.streak_best
        elif leaderboard_type == 'achievements':
            user_rank = UserStats.objects.filter(achievements_unlocked__gt=user_stats.achievements_unlocked).count() + 1
            user_score = user_stats.achievements_unlocked
        else:
            user_rank = 0
            user_score = 0
    except UserStats.DoesNotExist:
        user_rank = 0
        user_score = 0
    
    context = {
        'leaderboard_entries': page_obj,
        'leaderboard_type': leaderboard_type,
        'period': period,
        'user_rank': user_rank,
        'user_score': user_score,
        'page_title': 'Leaderboard'
    }
    
    return render(request, 'achievements/leaderboard.html', context)


@login_required
@require_http_methods(["GET"])
def user_progress_api(request):
    """API endpoint to get user progress data"""
    try:
        progress_summary = AchievementService.get_user_progress_summary(request.user)
        
        if progress_summary:
            # Convert to JSON-serializable format
            response_data = {
                'success': True,
                'data': {
                    'level': progress_summary['stats'].level,
                    'total_points': progress_summary['stats'].total_points,
                    'achievements_unlocked': progress_summary['unlocked_count'],
                    'total_achievements': progress_summary['total_achievements'],
                    'completion_percentage': progress_summary['completion_percentage'],
                    'user_rank': progress_summary['user_rank'],
                    'streak_current': progress_summary['stats'].streak_current,
                    'streak_best': progress_summary['stats'].streak_best,
                    'reports_created': progress_summary['stats'].reports_created,
                    'reports_validated': progress_summary['stats'].reports_validated,
                    'next_level_points': progress_summary['next_level_points'],
                }
            }
            
            # Add recent achievements
            recent_achievements = []
            for achievement in progress_summary['recent_achievements']:
                recent_achievements.append({
                    'name': achievement.achievement.name,
                    'description': achievement.achievement.description,
                    'icon': achievement.achievement.icon,
                    'tier': achievement.achievement.tier,
                    'points': achievement.achievement.points,
                    'unlocked_at': achievement.unlocked_at.isoformat() if achievement.unlocked_at else None
                })
            
            response_data['data']['recent_achievements'] = recent_achievements
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not retrieve user progress'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def notifications_api(request):
    """API endpoint to get achievement notifications"""
    try:
        notifications = AchievementService.get_unread_notifications(request.user)
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'achievement': {
                    'name': notification.achievement.name,
                    'icon': notification.achievement.icon,
                    'tier': notification.achievement.tier,
                    'points': notification.achievement.points,
                    'color': notification.achievement.get_tier_color()
                },
                'created_at': notification.created_at.isoformat(),
                'is_displayed': notification.is_displayed
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_notifications_read_api(request):
    """API endpoint to mark notifications as read"""
    try:
        notification_ids = request.POST.getlist('notification_ids', [])
        
        if notification_ids:
            AchievementService.mark_notifications_as_read(request.user, notification_ids)
        else:
            AchievementService.mark_notifications_as_read(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Notifications marked as read'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def track_action_api(request):
    """API endpoint to manually track user actions"""
    try:
        action_type = request.POST.get('action_type')
        
        if action_type == 'map_view':
            AchievementService.track_map_usage(request.user)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action type'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Action tracked successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def public_leaderboard_api(request):
    """Public API endpoint for leaderboard data"""
    try:
        leaderboard_type = request.GET.get('type', 'points')
        limit = min(int(request.GET.get('limit', 10)), 100)
        
        # Get top users
        if leaderboard_type == 'points':
            top_users = UserStats.objects.select_related('user').order_by('-total_points')[:limit]
            score_field = 'total_points'
        elif leaderboard_type == 'reports':
            top_users = UserStats.objects.select_related('user').order_by('-reports_created')[:limit]
            score_field = 'reports_created'
        elif leaderboard_type == 'achievements':
            top_users = UserStats.objects.select_related('user').order_by('-achievements_unlocked')[:limit]
            score_field = 'achievements_unlocked'
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid leaderboard type'
            }, status=400)
        
        leaderboard_data = []
        for rank, user_stats in enumerate(top_users, 1):
            leaderboard_data.append({
                'rank': rank,
                'username': user_stats.user.username,
                'level': user_stats.level,
                'score': getattr(user_stats, score_field),
                'achievements_unlocked': user_stats.achievements_unlocked
            })
        
        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard_data,
            'type': leaderboard_type,
            'count': len(leaderboard_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
