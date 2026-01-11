from django.db import models
from django.urls import reverse
from accounts.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products_by_category', args=[self.slug])
    
    class Meta:
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'
        ordering = ['name']


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Tên sản phẩm')
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(verbose_name='Mô tả')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Giá')
    sale_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='Giá khuyến mãi')
    
    image = models.ImageField(upload_to='products/', verbose_name='Hình ảnh')
    video_url = models.URLField(blank=True, null=True, verbose_name='Link video (YouTube)')
    
    stock = models.PositiveIntegerField(default=0, verbose_name='Tồn kho')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name='Sản phẩm nổi bật')
    
    views_count = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])
    
    @property
    def final_price(self):
        """Trả về giá cuối cùng (giá khuyến mãi nếu có)"""
        return self.sale_price if self.sale_price else self.price
    
    @property
    def discount_percent(self):
        """Tính phần trăm giảm giá"""
        if self.sale_price and self.price > 0:
            return int((1 - self.sale_price / self.price) * 100)
        return 0
    
    @property
    def average_rating(self):
        """Tính điểm đánh giá trung bình"""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0
    
    @property
    def youtube_embed_url(self):
        """Chuyển đổi URL YouTube thành embed URL"""
        if self.video_url:
            if 'youtube.com/watch?v=' in self.video_url:
                video_id = self.video_url.split('v=')[1].split('&')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1]
                return f'https://www.youtube.com/embed/{video_id}'
        return None
    
    class Meta:
        verbose_name = 'Sản phẩm'
        verbose_name_plural = 'Sản phẩm'
        ordering = ['-created_at']


class ProductImage(models.Model):
    """Nhiều hình ảnh cho một sản phẩm"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image of {self.product.name}"


class Review(models.Model):
    """Bình luận/đánh giá sản phẩm"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name='Đánh giá')
    comment = models.TextField(verbose_name='Bình luận')
    
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}*)"
    
    class Meta:
        verbose_name = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Mỗi user chỉ đánh giá 1 lần/sản phẩm