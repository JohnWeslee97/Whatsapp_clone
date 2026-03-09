from django.contrib import admin
from .models import Message, Profile

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'content', 'timestamp', 'is_read']
    list_filter  = ['is_read', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'content']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_online', 'last_seen']
    list_filter  = ['is_online']
    search_fields = ['user__username']