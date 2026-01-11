import openai
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

from products.models import Product, Category


@login_required
def ai_chat_view(request):
    """Trang chat với AI"""
    return render(request, 'ai_assistant/chat.html')


@require_POST
@login_required
def ai_recommend_view(request):
    """API để AI tư vấn sản phẩm"""
    user_message = request.POST.get('message', '')
    
    if not user_message:
        return JsonResponse({'error': 'Vui lòng nhập câu hỏi!'}, status=400)
    
    # Get product context
    categories = list(Category.objects.filter(is_active=True).values_list('name', flat=True))
    products = Product.objects.filter(is_active=True)[:20]
    product_info = "\n".join([
        f"- {p.name}: {p.final_price:,.0f}đ - {p.category.name}"
        for p in products
    ])
    
    system_prompt = f"""
Bạn là trợ lý tư vấn phụ kiện điện thoại cho cửa hàng Phone Accessories Shop.
Nhiệm vụ: Tư vấn sản phẩm phù hợp với nhu cầu khách hàng.

Danh mục sản phẩm: {', '.join(categories)}

Một số sản phẩm đang bán:
{product_info}

Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt. Đề xuất sản phẩm cụ thể khi có thể.
    """
    
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_reply = response.choices[0].message.content
        
        return JsonResponse({
            'reply': ai_reply,
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Lỗi kết nối AI: {str(e)}',
            'status': 'error'
        }, status=500)