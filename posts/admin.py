from django.contrib import admin
from .models import Post, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    fields = ('name', 'slug', 'description')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'has_image', 'published', 'created_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content', 'meta_description')
    prepopulated_fields = {"slug": ("title",)}
    
    fieldsets = (
        ('Contenido Principal', {
            'fields': ('title', 'slug', 'category', 'excerpt', 'image', 'content', 'published')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',),
            'description': 'Optimización para motores de búsqueda'
        }),
    )
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Imagen'
