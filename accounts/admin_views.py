from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, Role
from products.models import Product, Category
from orders.models import Order, OrderItem, PaymentMethod
from cart.models import Coupon


def admin_required(view_func):
    """Decorator kiểm tra quyền admin"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, 'Bạn không có quyền truy cập trang này!')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard_view(request):
    """Dashboard admin"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Statistics
    total_users = User.objects.count()
    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    
    # Revenue
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Today's stats
    today_orders = Order.objects.filter(created_at__date=today).count()
    today_revenue = Order.objects.filter(
        created_at__date=today, 
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Pending orders
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Revenue chart data (last 30 days)
    daily_revenue = Order.objects.filter(
        status='completed',
        created_at__date__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total')
    ).order_by('date')
    
    # Best selling products
    best_sellers = Product.objects.filter(
        is_active=True
    ).order_by('-sold_count')[:5]
    
    # Order status distribution
    order_status_counts = Order.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'pending_orders': pending_orders,
        'daily_revenue': list(daily_revenue),
        'best_sellers': best_sellers,
        'order_status_counts': {item['status']: item['count'] for item in order_status_counts},
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_users_view(request):
    """Quản lý người dùng"""
    users = User.objects.all().order_by('-created_at')
    roles = Role.objects.all()
    
    # Filter
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role__name=role_filter)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(username__icontains=search)
    
    context = {
        'users': users,
        'roles': roles,
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def toggle_user_lock_view(request, user_id):
    """Khóa/mở khóa user"""
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'Không thể khóa chính mình!')
    else:
        user.is_locked = not user.is_locked
        user.save()
        action = 'khóa' if user.is_locked else 'mở khóa'
        messages.success(request, f'Đã {action} tài khoản {user.username}!')
    return redirect('admin_users')


@admin_required
def change_user_role_view(request, user_id):
    """Thay đổi vai trò user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        role_id = request.POST.get('role_id')
        role = get_object_or_404(Role, id=role_id)
        user.role = role
        user.save()
        messages.success(request, f'Đã cập nhật vai trò cho {user.username}!')
    return redirect('admin_users')


@admin_required
def admin_products_view(request):
    """Quản lý sản phẩm"""
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    # Filter
    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category__id=category_filter)
    
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'admin_panel/products.html', context)


@admin_required
def admin_product_create_view(request):
    """Thêm sản phẩm mới"""
    from products.forms import ProductForm
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm sản phẩm thành công!')
            return redirect('admin_products')
    else:
        form = ProductForm()
    
    return render(request, 'admin_panel/product_form.html', {'form': form, 'action': 'Thêm'})


@admin_required
def admin_product_edit_view(request, product_id):
    """Sửa sản phẩm"""
    from products.forms import ProductForm
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật sản phẩm thành công!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'admin_panel/product_form.html', {'form': form, 'product': product, 'action': 'Sửa'})


@admin_required
def admin_product_delete_view(request, product_id):
    """Xóa sản phẩm"""
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    messages.success(request, 'Đã xóa sản phẩm!')
    return redirect('admin_products')


@admin_required
def admin_orders_view(request):
    """Quản lý đơn hàng"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/orders.html', context)


@admin_required
def admin_order_detail_view(request, order_id):
    """Chi tiết đơn hàng"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin_panel/order_detail.html', {'order': order})


@admin_required
def update_order_status_view(request, order_id):
    """Cập nhật trạng thái đơn hàng"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Create notification for user
            from notifications.models import Notification
            status_display = dict(Order.STATUS_CHOICES)[new_status]
            Notification.objects.create(
                user=order.user,
                title='Cập nhật đơn hàng',
                message=f'Đơn hàng #{order.id} đã chuyển sang trạng thái: {status_display}',
                notification_type='order',
                link=f'/orders/detail/{order.id}/'
            )
            
            messages.success(request, 'Cập nhật trạng thái đơn hàng thành công!')
    
    return redirect('admin_order_detail', order_id=order_id)


@admin_required
def admin_statistics_view(request):
    """Thống kê - Báo cáo"""
    today = timezone.now().date()
    
    # Date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = today - timedelta(days=30)
    if not end_date:
        end_date = today
    
    # Revenue by month
    monthly_revenue = Order.objects.filter(
        status='completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total'),
        order_count=Count('id')
    ).order_by('month')
    
    # Top products
    top_products = OrderItem.objects.filter(
        order__status='completed'
    ).values(
        'product__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_sold')[:10]
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    
    # Revenue by category
    revenue_by_category = OrderItem.objects.filter(
        order__status='completed'
    ).values(
        'product__category__name'
    ).annotate(
        total=Sum('price')
    ).order_by('-total')
    
    context = {
        'monthly_revenue': list(monthly_revenue),
        'top_products': list(top_products),
        'orders_by_status': list(orders_by_status),
        'revenue_by_category': list(revenue_by_category),
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_panel/statistics.html', context)


@admin_required
def admin_coupons_view(request):
    """Quản lý mã giảm giá"""
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/coupons.html', {'coupons': coupons})