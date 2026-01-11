from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

from cart.cart import Cart
from cart.models import Coupon
from products.models import Product
from .models import Order, OrderItem, PaymentMethod
from .forms import OrderCreateForm
from notifications.models import Notification


@login_required
def checkout_view(request):
    """Trang thanh toán"""
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, 'Giỏ hàng của bạn đang trống!')
        return redirect('product_list')
    
    # Get coupon if applied
    coupon = None
    discount = 0
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount = coupon.calculate_discount(cart.get_total_price())
        except Coupon.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = cart.get_total_price()
            order.shipping_fee = 30000  # Fixed shipping fee
            order.discount = discount
            if coupon:
                order.coupon = coupon
                coupon.used_count += 1
                coupon.save()
            order.total = order.subtotal + order.shipping_fee - order.discount
            order.save()
            
            # Create order items
            for item in cart:
                product = item['product']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    price=item['price']
                )
                # Update stock
                product.stock -= item['quantity']
                product.sold_count += item['quantity']
                product.save()
            
            # Clear cart and coupon
            cart.clear()
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title='Đặt hàng thành công!',
                message=f'Đơn hàng #{order.id} đã được tạo. Tổng tiền: {order.total:,.0f}đ',
                notification_type='order'
            )
            
            # Send confirmation email
            send_mail(
                subject=f'Xác nhận đơn hàng #{order.id} - Phone Accessories Shop',
                message=f'''
Xin chào {order.full_name},

Đơn hàng #{order.id} của bạn đã được tạo thành công!

Chi tiết đơn hàng:
- Tổng tiền: {order.total:,.0f}đ
- Phương thức thanh toán: {order.payment_method.name}
- Địa chỉ giao hàng: {order.address}

Chúng tôi sẽ liên hệ với bạn sớm nhất.

Trân trọng,
Phone Accessories Shop
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
            
            messages.success(request, 'Đặt hàng thành công!')
            return redirect('order_success', order_id=order.id)
    else:
        # Pre-fill form with user data
        initial = {
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.phone or '',
            'email': request.user.email,
            'address': request.user.address or '',
            'latitude': request.user.latitude,
            'longitude': request.user.longitude,
        }
        form = OrderCreateForm(initial=initial)
    
    context = {
        'cart': cart,
        'form': form,
        'coupon': coupon,
        'discount': discount,
        'shipping_fee': 30000,
        'total': cart.get_total_price() + 30000 - discount,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_success_view(request, order_id):
    """Trang đặt hàng thành công"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_history_view(request):
    """Lịch sử đơn hàng"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    """Chi tiết đơn hàng"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def cancel_order_view(request, order_id):
    """Hủy đơn hàng"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status not in ['pending', 'approved']:
        messages.error(request, 'Không thể hủy đơn hàng ở trạng thái này!')
        return redirect('order_detail', order_id=order.id)
    
    # Restore stock
    for item in order.items.all():
        item.product.stock += item.quantity
        item.product.sold_count -= item.quantity
        item.product.save()
    
    order.status = 'cancelled'
    order.save()
    
    Notification.objects.create(
        user=request.user,
        title='Đơn hàng đã hủy',
        message=f'Đơn hàng #{order.id} đã được hủy thành công.',
        notification_type='order'
    )
    
    messages.info(request, 'Đã hủy đơn hàng!')
    return redirect('order_history')


@login_required
def buy_now_view(request, product_id):
    """Mua ngay - Không qua giỏ hàng"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > product.stock:
        messages.error(request, f'Chỉ còn {product.stock} sản phẩm trong kho!')
        return redirect('product_detail', slug=product.slug)
    
    # Store in session for checkout
    request.session['buy_now'] = {
        'product_id': product.id,
        'quantity': quantity,
        'price': str(product.final_price)
    }
    
    return redirect('buy_now_checkout')


@login_required  
def buy_now_checkout_view(request):
    """Checkout cho mua ngay"""
    buy_now_data = request.session.get('buy_now')
    if not buy_now_data:
        return redirect('product_list')
    
    product = get_object_or_404(Product, id=buy_now_data['product_id'])
    quantity = buy_now_data['quantity']
    price = product.final_price
    subtotal = price * quantity
    shipping_fee = 30000
    total = subtotal + shipping_fee
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = subtotal
            order.shipping_fee = shipping_fee
            order.total = total
            order.save()
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
            
            # Update stock
            product.stock -= quantity
            product.sold_count += quantity
            product.save()
            
            # Clear session
            del request.session['buy_now']
            
            Notification.objects.create(
                user=request.user,
                title='Đặt hàng thành công!',
                message=f'Đơn hàng #{order.id} đã được tạo.',
                notification_type='order'
            )
            
            messages.success(request, 'Đặt hàng thành công!')
            return redirect('order_success', order_id=order.id)
    else:
        initial = {
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.phone or '',
            'email': request.user.email,
            'address': request.user.address or '',
        }
        form = OrderCreateForm(initial=initial)
    
    context = {
        'product': product,
        'quantity': quantity,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'form': form,
    }
    return render(request, 'orders/buy_now_checkout.html', context)