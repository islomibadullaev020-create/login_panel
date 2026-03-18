# urls.py
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Login sahifasi
    path('', login, name='login'),

    # Home sahifasi
    path('home/', home, name='home'),

    # Register sahifasi
    path('register/', register, name='register'),

    # Logout
    path('logout/', logout_view, name='logout'),

    # Movie detail page
    path('movie/<int:id>/', movie_detail, name='movie_detail'),
    path('search/', search, name='search'),
    path('profile/', profile, name='profile'),
    path('check-username/', check_username, name='check_username'),
    # Profile page
    path('profile/', profile, name='profile'),

    # AJAX: Username tekshirish
    # path('check-username/', check_username, name='check_username'),
    path('chat/', chat, name='chat'),
    path('ban_user/<int:user_id>/', ban_user, name='ban_user'),
    path('edit_message/<int:message_id>/', edit_message, name='edit_message'),
    path('delete_message/<int:message_id>/', delete_message, name='delete_message'),
    path('make-vip/<int:user_id>/',make_vip, name='make_vip'),
    path('check-username/', check_username, name='check_username'),
]



# Media fayllarini ishlatish (DEBUG rejimida)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
