from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from products.models import Product
from .cart import Cart
from .models import Coupon


def cart_detail(request):
    """Xem giỏ hàng"""
    cart = Cart(request)
    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount = 0
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount = coupon.calculate_discount(cart.get_total_price())
            else:
                del request.session['coupon_code']
                coupon = None
        except Coupon.DoesNotExist:
            pass
    
    context = {
        'cart': cart,
        'coupon': coupon,
        'discount': discount,
        'total_after_discount': cart.get_total_price() - discount,
    }
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def cart_add(request, product_id):
    """Thêm sản phẩm vào giỏ hàng"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override') == 'true'
    
    # Kiểm tra tồn kho
    if quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': f'Chỉ còn {product.stock} sản phẩm trong kho!'
            })
        messages.error(request, f'Chỉ còn {product.stock} sản phẩm trong kho!')
        return redirect('product_detail', slug=product.slug)
    
    cart.add(product=product, quantity=quantity, override_quantity=override)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'Đã thêm {product.name} vào giỏ hàng!',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    
    messages.success(request, f'Đã thêm {product.name} vào giỏ hàng!')
    return redirect('cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    
    messages.info(request, 'Đã xóa sản phẩm khỏi giỏ hàng!')
    return redirect('cart_detail')


@require_POST
def apply_coupon(request):
    """Áp dụng mã giảm giá"""
    code = request.POST.get('coupon_code', '').strip().upper()
    cart = Cart(request)
    
    try:
        coupon = Coupon.objects.get(code=code)
        
        if not coupon.is_valid():
            messages.error(request, 'Mã giảm giá không hợp lệ hoặc đã hết hạn!')
            return redirect('cart_detail')
        
        if cart.get_total_price() < coupon.min_order_amount:
            messages.error(request, f'Đơn hàng tối thiểu {coupon.min_order_amount:,.0f}đ để sử dụng mã này!')
            return redirect('cart_detail')
        
        request.session['coupon_code'] = code
        discount = coupon.calculate_discount(cart.get_total_price())
        messages.success(request, f'Áp dụng mã giảm giá thành công! Giảm {discount:,.0f}đ')
        
    except Coupon.DoesNotExist:
        messages.error(request, 'Mã giảm giá không tồn tại!')
    
    return redirect('cart_detail')


@require_POST
def remove_coupon(request):
    """Xóa mã giảm giá"""
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    messages.info(request, 'Đã xóa mã giảm giá!')
    return redirect('cart_detail')