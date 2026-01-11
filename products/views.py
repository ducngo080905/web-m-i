from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse

from .models import Product, Category, Review
from .forms import ProductSearchForm, ReviewForm


def home_view(request):
    """Trang chủ"""
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    best_sellers = Product.objects.filter(is_active=True).order_by('-sold_count')[:4]
    
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'categories': categories,
        'best_sellers': best_sellers,
    }
    return render(request, 'home.html', context)


def product_list_view(request):
    """Danh sách sản phẩm với tìm kiếm và lọc"""
    products = Product.objects.filter(is_active=True)
    form = ProductSearchForm(request.GET)
    
    if form.is_valid():
        # Tìm kiếm theo từ khóa
        q = form.cleaned_data.get('q')
        if q:
            products = products.filter(
                Q(name__icontains=q) | 
                Q(description__icontains=q) |
                Q(category__name__icontains=q)
            )
        
        # Lọc theo danh mục
        category = form.cleaned_data.get('category')
        if category:
            products = products.filter(category=category)
        
        # Lọc theo giá
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Sắp xếp
        sort = form.cleaned_data.get('sort')
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'name':
            products = products.order_by('name')
        elif sort == 'best_seller':
            products = products.order_by('-sold_count')
    
    # Phân trang
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'form': form,
        'categories': categories,
    }
    return render(request, 'products/product_list.html', context)


def product_detail_view(request, slug):
    """Chi tiết sản phẩm với bình luận"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Tăng lượt xem
    product.views_count += 1
    product.save(update_fields=['views_count'])
    
    # Lấy đánh giá
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Sản phẩm liên quan
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Form đánh giá
    review_form = ReviewForm()
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'review_form': review_form,
        'user_review': user_review,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def add_review_view(request, product_id):
    """Thêm đánh giá sản phẩm"""
    product = get_object_or_404(Product, id=product_id)
    
    # Kiểm tra đã đánh giá chưa
    existing_review = Review.objects.filter(product=product, user=request.user).first()
    if existing_review:
        messages.warning(request, 'Bạn đã đánh giá sản phẩm này rồi!')
        return redirect('product_detail', slug=product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Cảm ơn bạn đã đánh giá!')
    
    return redirect('product_detail', slug=product.slug)


def products_by_category_view(request, slug):
    """Sản phẩm theo danh mục"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'products/products_by_category.html', context)


def search_products_api(request):
    """API tìm kiếm sản phẩm (cho autocomplete)"""
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q),
        is_active=True
    )[:10]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'price': str(p.final_price),
        'image': p.image.url if p.image else '',
        'url': p.get_absolute_url(),
    } for p in products]
    
    return JsonResponse({'results': results})