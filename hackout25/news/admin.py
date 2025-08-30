from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'likes', 'published', 'category')
    search_fields = ('title', 'description')
    list_filter = ('category', 'published','likes',)
    ordering = ('-published','-likes',)
    list_editable = ('likes',)

