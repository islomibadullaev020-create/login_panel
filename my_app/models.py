from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
import subprocess
from django.utils import timezone



# ==========================
# Kategoriya modeli
# ==========================
class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ==========================
# Foydalanuvchi modeli
# ==========================
class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_banned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)

    def __str__(self):
        return self.username if self.username else f"User-{self.id}"

class VipUserTanlash(models.Model):
    user = models.OneToOneField(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='vip_data'
    )
    is_vip = models.BooleanField(default=False)
    vip_expire = models.DateTimeField(null=True, blank=True)

    def vip_active(self):
        """
        Agar foydalanuvchi VIP bo'lsa va vip_expire belgilanggan bo'lsa,
        VIP muddati tugamagan bo'lsa True qaytaradi.
        """
        return self.is_vip and self.vip_expire and self.vip_expire > timezone.now()

    def __str__(self):
        return f"{self.user.username} - VIP" if self.user.username else f"User-{self.user.id} - VIP"


# ==========================
# Kino modeli
# ==========================
class Movie(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='movies/')
    description = models.TextField(blank=True, null=True)

    telegram_code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Telegram bot start parametri (masalan: 28, berserk, naruto123)"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movies"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def telegram_link(self):
        return f"https://t.me/Ani_best_bot?start={self.telegram_code}"


# ==========================
# Kino qismi (episode)
# ==========================
class MovieEpisode(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='episodes'
    )
    episode_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    video = models.FileField(upload_to='videos/')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['episode_number']

    def __str__(self):
        return f"{self.movie.title} - {self.episode_number}-qism - {self.title}"


# ==========================
# Video faststart optimizatsiya
# ==========================
@receiver(post_save, sender=MovieEpisode)
def make_video_web_optimized(sender, instance, **kwargs):
    if not instance.video:
        return

    video_path = instance.video.path
    tmp_path = video_path + ".tmp.mp4"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-c", "copy",
        "-movflags", "faststart",
        tmp_path
    ]

    try:
        subprocess.run(command, check=True)
        os.replace(tmp_path, video_path)
        print(f"[INFO] {instance.video.name} faststart qilindi")
    except Exception as e:
        print(f"[ERROR] Video faststart qilishda xato: {e}")


# ==========================
# Sayt sozlamalari
# ==========================
class SiteSettings(models.Model):
    background_video = models.FileField(
        upload_to='backgrounds/',
        blank=True,
        null=True
    )
    background_image = models.ImageField(
        upload_to='backgrounds/',
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Sayt Sozlamalari"


class MP3(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='mp3/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ==========================
# CHAT MODELI
# ==========================
class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='replies'
    )

    def local_created_at(self):
        from django.utils.timezone import localtime
        import pytz
        uz_time = pytz.timezone('Asia/Tashkent')
        return localtime(self.created_at, uz_time)

    # Admin va ban tekshiruvi (viewlarda ishlatish uchun)
    def can_delete(self, current_user):
        """
        Agar xabar egasi yoki admin foydalanuvchi bo'lsa, xabarni o'chirishi mumkin
        """
        return self.user == current_user or current_user.is_admin_user

    def can_reply(self, current_user):
        """
        Agar foydalanuvchi ban bo'lmagan bo'lsa, reply qilishi mumkin
        """
        return not current_user.is_banned
