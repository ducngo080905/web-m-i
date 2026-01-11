from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Quản trị viên'),
        ('user', 'Người dùng'),
    ]
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = 'Vai trò'
        verbose_name_plural = 'Vai trò'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Số điện thoại')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    address = models.TextField(blank=True, null=True, verbose_name='Địa chỉ')
    
    # Map coordinates for delivery
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Theme preferences
    theme_brightness = models.IntegerField(default=100, verbose_name='Độ sáng nền (%)')
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username
    
    @property
    def is_admin(self):
        return self.role and self.role.name == 'admin' or self.is_superuser
    
    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'


class PasswordResetToken(models.Model):
    """Token để đặt lại mật khẩu qua email/SMS"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Reset token for {self.user.username}"