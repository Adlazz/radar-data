from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Post, Category

def post_list(request):
    posts = Post.objects.filter(published=True).select_related('category')
    
    # Paginación
    paginator = Paginator(posts, 6)  # 6 posts por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'posts/post_list.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, published=True)
    return render(request, 'posts/post_detail.html', {'post': post})
