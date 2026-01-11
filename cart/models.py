from django.db import models
from accounts.models import User
from products.models import Product


class Coupon(models.Model):
    """Mã giảm giá"""
    code = models.CharField(max_length=50, unique=True, verbose_name='Mã giảm giá')
    discount_type = models.CharField(max_length=20, choices=[
        ('percent', 'Phần trăm'),
        ('fixed', 'Số tiền cố định'),
    ], default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=0)
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Đơn hàng tối thiểu')
    max_discount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='Giảm tối đa')
    
    usage_limit = models.PositiveIntegerField(default=100, verbose_name='Số lần sử dụng tối đa')
    used_count = models.PositiveIntegerField(default=0, verbose_name='Đã sử dụng')
    
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_to and
            self.used_count < self.usage_limit
        )
    
    def calculate_discount(self, order_total):
        """Tính số tiền giảm"""
        if order_total < self.min_order_amount:
            return 0
        
        if self.discount_type == 'percent':
            discount = order_total * self.discount_value / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value
        
        return min(discount, order_total)
    
    class Meta:
        verbose_name = 'Mã giảm giá'
        verbose_name_plural = 'Mã giảm giá'