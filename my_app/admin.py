from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# ==========================
# CustomUser admin
# ==========================
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff','is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'phone', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

# ==========================
# VipUserTanlash admin
# ==========================
class VipUserTanlashAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_vip', 'vip_expire')  # Ro'yxatda ID ko'rinadi
    fields = ('user', 'is_vip', 'vip_expire')  # Formda editable maydonlar
    readonly_fields = ('id',)  # Agar formda ID ni ko'rsatmoqchi bo'lsangiz
    search_fields = ('id',)  # faqat ID orqali qidiradi

# ==========================
# MovieEpisode inline admin
# ==========================
class MovieEpisodeInline(admin.TabularInline):
    model = MovieEpisode
    extra = 1  # Default 1 qator qo‘shiladi
    fields = ('episode_number', 'title', 'video', 'description')  # Qaysi maydonlar ko‘rinadi
    readonly_fields = ()
    show_change_link = True

# ==========================
# Movie admin
# ==========================

class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'telegram_code', 'created_at')
    search_fields = ('title', 'telegram_code')
    list_filter = ('created_at',)
    inlines = [MovieEpisodeInline]

# ==========================
# SiteSettings admin
# ==========================
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'background_video', 'background_image', 'updated_at')

# ==========================
# MP3 admin
# ==========================
class MP3Admin(admin.ModelAdmin):
    list_display = ('title', 'file', 'created_at')
    search_fields = ('title',)


# =========================
# ChatMessage admin
# =========================
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message_preview', 'created_at', 'edited', 'reply_to')
    list_filter = ('edited', 'created_at')
    search_fields = ('message', 'user__username')
    ordering = ('-created_at',)

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


# ==========================
# Register models with admin
# ==========================
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieEpisode)  # Agar alohida ham ko‘rish xohlasa
admin.site.register(SiteSettings, SiteSettingsAdmin)
admin.site.register(MP3, MP3Admin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(Category)
admin.site.register(VipUserTanlash, VipUserTanlashAdmin)