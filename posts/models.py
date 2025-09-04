from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text='Descripción breve de la categoría')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Categoría')
    excerpt = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True, help_text='Imagen ilustrativa del post')
    content = models.TextField()
    
    # SEO fields
    meta_description = models.CharField(max_length=160, blank=True, help_text='Descripción para motores de búsqueda (máx. 160 caracteres)')
    meta_keywords = models.CharField(max_length=255, blank=True, help_text='Palabras clave separadas por comas')
    
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class NewsGeneration(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SEARCHING', 'Buscando noticias'),
        ('GENERATING', 'Generando contenido'),
        ('COMPLETED', 'Completado'),
        ('ERROR', 'Error'),
        ('PUBLISHED', 'Publicado'),
    ]
    
    tags = models.CharField(max_length=500, help_text='Tags separados por comas para buscar noticias')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Contenido generado por IA
    generated_title = models.CharField(max_length=200, blank=True)
    generated_excerpt = models.CharField(max_length=300, blank=True)
    generated_content = models.TextField(blank=True, help_text='Contenido en formato HTML')
    generated_meta_description = models.CharField(max_length=160, blank=True)
    generated_meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Metadata de fuentes
    source_articles = models.JSONField(default=list, help_text='Lista de artículos fuente con URLs y metadata')
    total_sources_found = models.IntegerField(default=0)
    
    # Gestión
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Vinculación con post publicado
    published_post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Post publicado')
    
    # Campos de error
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Generación de Noticia IA'
        verbose_name_plural = 'Generaciones de Noticias IA'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"IA Gen: {self.tags[:50]}... ({self.get_status_display()})"
    
    @property
    def tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    @property
    def can_publish(self):
        return self.status == 'COMPLETED' and self.generated_title and self.generated_content
    
