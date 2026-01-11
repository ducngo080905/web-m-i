import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from accounts.models import User
from products.models import Product
from cart.models import Coupon


class PaymentMethod(models.Model):
    """Phương thức thanh toán"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome icon class
    is_active = models.BooleanField(default=True)
    
    # Bank info for QR transfer
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    bank_holder = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('approved', 'Đã xác nhận'),
        ('shipping', 'Đang giao hàng'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Shipping info
    full_name = models.CharField(max_length=100, verbose_name='Họ tên')
    phone = models.CharField(max_length=15, verbose_name='Số điện thoại')
    email = models.EmailField()
    address = models.TextField(verbose_name='Địa chỉ giao hàng')
    
    # Map coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    note = models.TextField(blank=True, verbose_name='Ghi chú')
    
    # Payment
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    is_paid = models.BooleanField(default=False)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Coupon
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Tổng tiền')
    
    # QR Code for payment
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.username}"
    
    def generate_qr_code(self):
        """Tạo QR code thanh toán"""
        if self.payment_method and self.payment_method.bank_account:
            # Tạo nội dung QR theo chuẩn VietQR
            qr_data = f"""
Bank: {self.payment_method.bank_name}
Account: {self.payment_method.bank_account}
Name: {self.payment_method.bank_holder}
Amount: {self.total}
Content: DH{self.id} - {self.full_name}
            """.strip()
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            filename = f'order_{self.id}_qr.png'
            self.qr_code.save(filename, File(buffer), save=False)
    
    def save(self, *args, **kwargs):
        # Calculate total
        if not self.total:
            self.total = self.subtotal + self.shipping_fee - self.discount
        
        # Generate QR on first save for bank transfer
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.payment_method and self.payment_method.code == 'bank_transfer':
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])
    
    class Meta:
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    
    @property
    def total_price(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    class Meta:
        verbose_name = 'Chi tiết đơn hàng'
        verbose_name_plural = 'Chi tiết đơn hàng'