import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse

from .models import User, PasswordResetToken, Role
from .forms import (
    CustomUserCreationForm, 
    CustomLoginForm, 
    ProfileUpdateForm,
    ForgotPasswordForm,
    ResetPasswordForm
)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Assign default user role
            user_role, _ = Role.objects.get_or_create(name='user')
            user.role = user_role
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Đăng ký thành công! Chào mừng bạn!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_locked:
                messages.error(request, 'Tài khoản của bạn đã bị khóa!')
                return redirect('login')
            login(request, user)
            messages.success(request, f'Chào mừng {user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = CustomLoginForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất!')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật hồ sơ thành công!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'auth/profile.html', {'form': form})


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data['email_or_phone']
            
            # Find user by email or phone
            user = User.objects.filter(email=email_or_phone).first()
            if not user:
                user = User.objects.filter(phone=email_or_phone).first()
            
            if user:
                # Generate token
                token = secrets.token_urlsafe(32)
                expires_at = timezone.now() + timedelta(hours=1)
                
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Send email
                reset_link = f"{request.scheme}://{request.get_host()}/user/reset-password/{token}/"
                send_mail(
                    subject='Đặt lại mật khẩu - Phone Accessories Shop',
                    message=f'''
Xin chào {user.username},

Bạn đã yêu cầu đặt lại mật khẩu. Vui lòng click vào link bên dưới:
{reset_link}

Link này sẽ hết hạn sau 1 giờ.

Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.

Trân trọng,
Phone Accessories Shop
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Link đặt lại mật khẩu đã được gửi đến email của bạn!')
            else:
                messages.error(request, 'Không tìm thấy tài khoản với thông tin này!')
            return redirect('forgot_password')
    else:
        form = ForgotPasswordForm()
    return render(request, 'auth/forgot_password.html', {'form': form})


def reset_password_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token, is_used=False)
    
    # Check if token expired
    if timezone.now() > reset_token.expires_at:
        messages.error(request, 'Link đặt lại mật khẩu đã hết hạn!')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, 'Mật khẩu đã được đặt lại thành công! Vui lòng đăng nhập.')
            return redirect('login')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'auth/reset_password.html', {'form': form, 'token': token})


@login_required
def update_location(request):
    """API để cập nhật vị trí giao hàng từ bản đồ"""
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        address = request.POST.get('address', '')
        
        request.user.latitude = lat
        request.user.longitude = lng
        if address:
            request.user.address = address
        request.user.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def update_theme_brightness(request):
    """API để cập nhật độ sáng nền"""
    if request.method == 'POST':
        brightness = request.POST.get('brightness', 100)
        request.user.theme_brightness = int(brightness)
        request.user.save()
        return JsonResponse({'status': 'success', 'brightness': brightness})
    return JsonResponse({'status': 'error'}, status=400)