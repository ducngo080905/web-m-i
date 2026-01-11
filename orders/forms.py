from django import forms
from .models import Order, PaymentMethod


class OrderCreateForm(forms.ModelForm):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        empty_label=None
    )
    
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'email', 'address', 'note', 'payment_method', 'latitude', 'longitude']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ghi chú cho đơn hàng...'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }