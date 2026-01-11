from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role
from products.models import Category, Product
from orders.models import PaymentMethod
from cart.models import Coupon
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample data'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create Roles
        admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Quản trị viên'})
        user_role, _ = Role.objects.get_or_create(name='user', defaults={'description': 'Người dùng'})
        
        # Create Admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role=admin_role
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin/admin123'))
        
        # Create Sample Users
        users_data = [
            {'username': 'user1', 'email': 'user1@example.com', 'phone': '0901234567'},
            {'username': 'user2', 'email': 'user2@example.com', 'phone': '0902345678'},
            {'username': 'user3', 'email': 'user3@example.com', 'phone': '0903456789'},
        ]
        for data in users_data:
            if not User.objects.filter(username=data['username']).exists():
                User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='password123',
                    phone=data['phone'],
                    role=user_role
                )
        
        # Create Categories
        categories_data = [
            {'name': 'Ốp lưng', 'slug': 'op-lung'},
            {'name': 'Tai nghe', 'slug': 'tai-nghe'},
            {'name': 'Sạc & Cáp', 'slug': 'sac-cap'},
            {'name': 'Pin dự phòng', 'slug': 'pin-du-phong'},
            {'name': 'Miếng dán màn hình', 'slug': 'mieng-dan'},
            {'name': 'Phụ kiện khác', 'slug': 'phu-kien-khac'},
        ]
        categories = []
        for data in categories_data:
            cat, _ = Category.objects.get_or_create(slug=data['slug'], defaults={'name': data['name']})
            categories.append(cat)
        
        # Create Products
        products_data = [
            # Ốp lưng
            {'name': 'Ốp lưng iPhone 15 Pro Max trong suốt', 'price': 150000, 'sale_price': 99000, 'category': 0},
            {'name': 'Ốp lưng Samsung S24 Ultra chống sốc', 'price': 250000, 'sale_price': 179000, 'category': 0},
            {'name': 'Ốp lưng Xiaomi 14 Pro silicon', 'price': 120000, 'category': 0},
            {'name': 'Ốp lưng OPPO Find X6 Pro cao cấp', 'price': 200000, 'sale_price': 150000, 'category': 0},
            
            # Tai nghe
            {'name': 'Tai nghe Bluetooth TWS Pro', 'price': 450000, 'sale_price': 299000, 'category': 1},
            {'name': 'Tai nghe AirPods Pro 2 Rep 1:1', 'price': 650000, 'sale_price': 499000, 'category': 1},
            {'name': 'Tai nghe gaming có dây 7.1', 'price': 350000, 'category': 1},
            {'name': 'Tai nghe chụp tai Bluetooth', 'price': 550000, 'sale_price': 399000, 'category': 1},
            
            # Sạc & Cáp
            {'name': 'Sạc nhanh 65W GaN', 'price': 450000, 'sale_price': 350000, 'category': 2},
            {'name': 'Cáp Type-C to Lightning 2m', 'price': 150000, 'category': 2},
            {'name': 'Sạc không dây 15W', 'price': 250000, 'sale_price': 199000, 'category': 2},
            {'name': 'Hub USB-C 7 in 1', 'price': 550000, 'sale_price': 450000, 'category': 2},
            
            # Pin dự phòng
            {'name': 'Pin sạc dự phòng 20000mAh', 'price': 450000, 'sale_price': 350000, 'category': 3},
            {'name': 'Pin sạc dự phòng mini 10000mAh', 'price': 300000, 'category': 3},
            {'name': 'Pin sạc nhanh PD 30000mAh', 'price': 750000, 'sale_price': 599000, 'category': 3},
            
            # Miếng dán
            {'name': 'Kính cường lực iPhone 15 Pro', 'price': 100000, 'sale_price': 79000, 'category': 4},
            {'name': 'Kính cường lực Samsung S24', 'price': 120000, 'sale_price': 89000, 'category': 4},
            {'name': 'Miếng dán hydrogel', 'price': 80000, 'category': 4},
            
            # Phụ kiện khác
            {'name': 'Giá đỡ điện thoại ô tô', 'price': 200000, 'sale_price': 150000, 'category': 5},
            {'name': 'Gimbal điện thoại 3 trục', 'price': 1200000, 'sale_price': 899000, 'category': 5},
        ]
        
        for i, data in enumerate(products_data):
            if not Product.objects.filter(name=data['name']).exists():
                Product.objects.create(
                    name=data['name'],
                    slug=f"product-{i+1}",
                    category=categories[data['category']],
                    description=f"Mô tả chi tiết cho {data['name']}. Sản phẩm chất lượng cao, chính hãng.",
                    price=data['price'],
                    sale_price=data.get('sale_price'),
                    stock=random.randint(10, 100),
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    sold_count=random.randint(0, 50),
                    views_count=random.randint(10, 500),
                )
        
        # Create Payment Methods
        payment_methods = [
            {
                'name': 'Thanh toán khi nhận hàng (COD)',
                'code': 'cod',
                'icon': 'bi-cash-stack',
                'description': 'Thanh toán tiền mặt khi nhận hàng'
            },
            {
                'name': 'Chuyển khoản ngân hàng',
                'code': 'bank_transfer',
                'icon': 'bi-bank',
                'description': 'Chuyển khoản qua ngân hàng',
                'bank_name': 'Vietcombank',
                'bank_account': '1234567890',
                'bank_holder': 'PHONE ACCESSORIES SHOP'
            },
            {
                'name': 'Ví điện tử MoMo',
                'code': 'momo',
                'icon': 'bi-wallet2',
                'description': 'Thanh toán qua ví MoMo'
            },
        ]
        for data in payment_methods:
            PaymentMethod.objects.get_or_create(code=data['code'], defaults=data)
        
        # Create Coupons
        coupons_data = [
            {
                'code': 'WELCOME10',
                'discount_type': 'percent',
                'discount_value': 10,
                'min_order_amount': 200000,
                'max_discount': 50000,
                'usage_limit': 100,
            },
            {
                'code': 'FREESHIP',
                'discount_type': 'fixed',
                'discount_value': 30000,
                'min_order_amount': 300000,
                'usage_limit': 50,
            },
            {
                'code': 'SALE20',
                'discount_type': 'percent',
                'discount_value': 20,
                'min_order_amount': 500000,
                'max_discount': 100000,
                'usage_limit': 30,
            },
        ]
        for data in coupons_data:
            if not Coupon.objects.filter(code=data['code']).exists():
                Coupon.objects.create(
                    **data,
                    valid_from=timezone.now(),
                    valid_to=timezone.now() + timedelta(days=30)
                )
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))