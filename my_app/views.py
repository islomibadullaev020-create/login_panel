from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from datetime import timedelta
import pytz
from django.db.models import Max
from django.utils import timezone
from .models import *
import os
import subprocess


User = get_user_model()


# ==========================
# Register view
# ==========================
def register(request):
    site_settings = SiteSettings.objects.last()
    context = {'site_settings': site_settings}

    if request.method == "POST":
        username = request.POST.get('username').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Bu username allaqachon ishlatilgan")
            return redirect('register')
        if email and CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Bu email allaqachon ishlatilgan")
            return redirect('register')

        user = CustomUser(username=username, email=email)
        user.set_password(password)
        user.save()

        messages.success(request, "Akaunt muvaffaqiyatli yaratildi. Endi kirishingiz mumkin.")
        return redirect('login')

    return render(request, 'register.html', context)


# ==========================
# Login view
# ==========================
def login(request):
    site_settings = SiteSettings.objects.last()
    context = {'site_settings': site_settings}

    if request.method == "POST":
        username = request.POST.get('username').strip()
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['mp3_played'] = False
            return redirect('home')
        else:
            messages.error(request, "Username yoki parol noto‘g‘ri")
            return redirect('login')

    return render(request, 'login.html', context)


# ==========================
# Logout view
# ==========================
def logout_view(request):
    auth_logout(request)
    return redirect('login')


@login_required
def home(request):

    movies = Movie.objects.prefetch_related('episodes').annotate(
        last_episode=Max('episodes__created_at')
    ).order_by('-last_episode')

    # 🔥 QO‘SHILGAN QATOR
    categories = Category.objects.all()

    for movie in movies:
        if hasattr(movie, 'telegram_code') and movie.telegram_code:
            movie.telegram_link = f"https://t.me/Ani_best_bot?start={movie.telegram_code}"
        else:
            movie.telegram_link = None

    try:
        mp3_obj = MP3.objects.latest('created_at')
        mp3_file = mp3_obj.file.url
    except MP3.DoesNotExist:
        mp3_file = None

    if not request.session.get('mp3_played', False):
        mp3_to_play = mp3_file
        request.session['mp3_played'] = True
    else:
        mp3_to_play = None

    total_users = User.objects.count()
    user_id = request.user.id

    context = {
        'movies': movies,
        'categories': categories,  # 🔥 QO‘SHILDI
        'mp3_file': mp3_to_play,
        'total_users': total_users,
        'user_id': user_id,
    }

    return render(request, 'home.html', context)


# ==========================
# Movie detail page
# ==========================
@login_required
def movie_detail(request, id):
    movie = get_object_or_404(Movie, id=id)
    episodes = movie.episodes.all().order_by('episode_number')

    for episode in episodes:
        video_path = os.path.join(settings.MEDIA_ROOT, episode.video.name)
        optimized_path = os.path.join(settings.MEDIA_ROOT, f"optimized_{episode.video.name}")

        if not os.path.exists(optimized_path):
            try:
                subprocess.run([
                    "ffmpeg",
                    "-i", video_path,
                    "-c", "copy",
                    "-movflags", "faststart",
                    optimized_path
                ], check=True)
                episode.video.name = f"optimized_{episode.video.name}"
                episode.save()
            except Exception as e:
                print(f"Video optimize qilishda xato: {e}")

    return render(request, 'movie_detail.html', {'movie': movie, 'episodes': episodes})


def check_username(request):
    username = request.GET.get('username', None)
    exists = CustomUser.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

# ==========================
# Profile
# ==========================
@login_required
def profile(request):
    user = request.user
    uz_time = pytz.timezone('Asia/Tashkent')
    date_joined_uz = localtime(user.date_joined, uz_time).strftime("%d-%m-%Y %H:%M:%S")

    try:
        total_users = CustomUser.objects.latest('id').id
    except CustomUser.DoesNotExist:
        total_users = 0

    # VIP holatini olish
    try:
        vip = user.vip_data
        vip_active = vip.vip_active()
    except VipUserTanlash.DoesNotExist:
        vip_active = False

    return render(request, 'profile.html', {
        'user': user,
        'date_joined_uz': date_joined_uz,
        'total_users': total_users,
        'vip_active': vip_active
    })


@login_required
def make_vip(request, user_id):
    # Faqat admin foydalanuvchi VIP bera oladi
    if not request.user.is_staff and not request.user.is_admin_user:
        return redirect('profile')

    # user obyekti olish
    user = get_object_or_404(CustomUser, id=user_id)

    # VipUserTanlash yozuvi mavjud bo'lmasa yaratish
    vip_record, created = VipUserTanlash.objects.get_or_create(user=user)
    vip_record.is_vip = True
    vip_record.vip_expire = timezone.now() + timedelta(days=30)  # 30 kunlik VIP
    vip_record.save()

    return redirect('profile')

# ==========================
# Search
# ==========================
@login_required
def search(request):
    query = request.GET.get('q', '').strip()

    if query:
        movies = Movie.objects.filter(title__icontains=query)
    else:
        movies = Movie.objects.all()

    return render(request, 'search.html', {
        'movies': movies,
        'query': query,
    })


# ==========================
# CHAT SECTION
# ==========================
@login_required
def chat(request):
    tz = pytz.timezone('Asia/Tashkent')
    messages_list = ChatMessage.objects.select_related('user', 'reply_to').order_by('created_at')

    # Har bir xabar uchun localtime hisoblash
    for msg in messages_list:
        msg.local_created_at = localtime(msg.created_at, tz)

    if request.method == "POST":
        # Agar foydalanuvchi ban qilingan bo'lsa, yozishga ruxsat yo'q
        if request.user.is_banned:
            messages.error(request, "Siz yozish huquqiga ega emassiz!")
            return redirect('chat')

        text = request.POST.get("message", "").strip()
        reply_to_id = request.POST.get("reply_to")
        reply_to_msg = None

        # reply_to_id ni int qilib olish va tekshirish
        if reply_to_id:
            try:
                reply_to_id_int = int(reply_to_id)
                reply_to_msg = ChatMessage.objects.filter(id=reply_to_id_int).first()
            except ValueError:
                reply_to_msg = None
        if request.user.is_banned:
            # agar foydalanuvchi ban qilingan bo'lsa
            messages.error(request, "Siz chatda yozish huquqiga ega emassiz.")
            return redirect('home')
        if text:
            new_msg = ChatMessage.objects.create(
                user=request.user,
                message=text,
                created_at=timezone.now(),
                reply_to=reply_to_msg
            )

            # Agar bu xabar reply bo‘lsa, xabar egasiga bildirishnoma yuborish
            if reply_to_msg and reply_to_msg.user != request.user:
                # Bu yerda real-time bildirishnoma uchun WebSocket, Telegram/email/notification qo‘shishingiz mumkin
                print(f"[INFO] {reply_to_msg.user.username} xabarga javob olindi: {new_msg.message}")

        return redirect('chat')

    return render(request, 'chat.html', {
        'messages': messages_list
    })


# ==========================
# CHAT EDIT
# ==========================
@login_required
def edit_message(request, message_id):
    msg = get_object_or_404(ChatMessage, id=message_id)

    # Faqat xabar egasi yoki admin tahrirlashi mumkin
    if request.user != msg.user and not request.user.is_admin_user:
        messages.error(request, "Siz bu xabarni tahrirlash huquqiga ega emassiz!")
        return redirect('chat')

    if request.method == "POST":
        new_text = request.POST.get("message", "").strip()
        if new_text:
            msg.message = new_text
            msg.edited = True
            msg.save()
    return redirect('chat')


# ==========================
# CHAT DELETE
# ==========================
@login_required
def delete_message(request, message_id):
    msg = get_object_or_404(ChatMessage, id=message_id)

    # Faqat xabar egasi yoki admin o'chirishi mumkin
    if request.user != msg.user and not request.user.is_admin_user:
        messages.error(request, "Siz bu xabarni o'chirish huquqiga ega emassiz!")
        return redirect('chat')

    msg.delete()
    return redirect('chat')

@login_required
def ban_user(request, user_id):
    if not request.user.is_admin_user:
        return redirect('chat')  # admin bo'lmagan foydalanuvchi cheklangan
    user_to_ban = get_object_or_404(CustomUser, id=user_id)
    if not user_to_ban.is_admin_user:
        user_to_ban.is_banned = True
        user_to_ban.save()
    return redirect('chat')

