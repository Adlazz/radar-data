from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import Post, Category, NewsGeneration
from .services_simple import SimpleNewsGenerationService, MockSimpleNewsGenerationService
from decouple import config

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


@admin.register(NewsGeneration)
class NewsGenerationAdmin(admin.ModelAdmin):
    list_display = ('id', 'tags_display', 'status_display', 'total_sources_found', 'created_by', 'created_at', 'actions_column')
    list_filter = ('status', 'created_by', 'created_at')
    search_fields = ('tags', 'generated_title', 'error_message')
    readonly_fields = ('created_by', 'created_at', 'completed_at', 'total_sources_found', 'source_articles', 'error_message', 'published_post')
    
    fieldsets = (
        ('Configuración', {
            'fields': ('tags', 'manual_urls', 'status', 'created_by', 'created_at')
        }),
        ('Resultados de Búsqueda', {
            'fields': ('total_sources_found', 'source_articles'),
            'classes': ('collapse',),
        }),
        ('Contenido Generado por IA', {
            'fields': ('generated_title', 'generated_excerpt', 'generated_content', 'generated_meta_description', 'generated_meta_keywords'),
            'classes': ('wide',),
        }),
        ('Estado y Errores', {
            'fields': ('completed_at', 'error_message', 'published_post'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        # Si es nueva generación, procesarla automáticamente
        if not change and obj.status == 'PENDING':
            try:
                # Decidir si usar OpenAI real o simulado
                api_key = config('OPENAI_API_KEY', default='')
                if api_key and api_key != 'your-openai-api-key-here' and len(api_key) > 20:
                    service = SimpleNewsGenerationService()
                    messages.info(request, f"Procesando con OpenAI real...")
                else:
                    service = MockSimpleNewsGenerationService()
                    messages.info(request, f"Procesando con IA simulada (configura OpenAI para usar IA real)...")
                
                service.process_news_generation(obj.id)
                messages.success(request, f"Generación #{obj.id} procesada exitosamente")
            except Exception as e:
                messages.error(request, f"Error procesando generación: {str(e)}")
    
    def tags_display(self, obj):
        if len(obj.tags) > 50:
            return obj.tags[:47] + "..."
        return obj.tags
    tags_display.short_description = 'Tags'
    
    def status_display(self, obj):
        colors = {
            'PENDING': 'orange',
            'SEARCHING': 'blue', 
            'GENERATING': 'purple',
            'COMPLETED': 'green',
            'ERROR': 'red',
            'PUBLISHED': 'darkgreen'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Estado'
    
    def actions_column(self, obj):
        buttons = []
        
        if obj.status == 'COMPLETED' and obj.can_publish:
            publish_url = reverse('admin:news_publish', args=[obj.pk])
            buttons.append(f'<a href="{publish_url}" class="button" style="background: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Publicar</a>')
        
        if obj.generated_content:
            preview_url = reverse('admin:news_preview', args=[obj.pk])
            buttons.append(f'<a href="{preview_url}" class="button" target="_blank" style="background: #79aec8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Vista Previa</a>')
        
        return format_html(''.join(buttons))
    actions_column.short_description = 'Acciones'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:news_id>/publish/', self.admin_site.admin_view(self.publish_news), name='news_publish'),
            path('<int:news_id>/preview/', self.admin_site.admin_view(self.preview_news), name='news_preview'),
        ]
        return custom_urls + urls
    
    def publish_news(self, request, news_id):
        """
        Publica la noticia generada como un nuevo Post
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_id)
            
            if not news_gen.can_publish:
                messages.error(request, "Esta generación no está lista para publicar")
                return redirect('admin:posts_newsgeneration_changelist')
            
            # Crear nuevo Post
            new_post = Post.objects.create(
                title=news_gen.generated_title,
                excerpt=news_gen.generated_excerpt,
                content=news_gen.generated_content,
                meta_description=news_gen.generated_meta_description,
                meta_keywords=news_gen.generated_meta_keywords,
                published=False  # Crear como borrador
            )
            
            # Actualizar NewsGeneration
            news_gen.published_post = new_post
            news_gen.status = 'PUBLISHED'
            news_gen.save()
            
            messages.success(request, f'Noticia publicada exitosamente como borrador: "{new_post.title}"')
            return redirect('admin:posts_post_change', new_post.id)
            
        except NewsGeneration.DoesNotExist:
            messages.error(request, "Generación no encontrada")
        except Exception as e:
            messages.error(request, f"Error al publicar: {str(e)}")
        
        return redirect('admin:posts_newsgeneration_changelist')
    
    def preview_news(self, request, news_id):
        """
        Muestra una vista previa del contenido generado
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_id)
            
            html_preview = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Vista Previa: {news_gen.generated_title}</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                    .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
                    .excerpt {{ font-style: italic; color: #555; border-left: 3px solid #ddd; padding-left: 15px; margin: 20px 0; }}
                    .content {{ margin-top: 30px; }}
                    .sources {{ margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 5px; }}
                    .sources h3 {{ margin-top: 0; }}
                    .source-item {{ margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <h1>{news_gen.generated_title}</h1>
                <div class="meta">
                    <strong>Tags:</strong> {news_gen.tags}<br>
                    <strong>Estado:</strong> {news_gen.get_status_display()}<br>
                    <strong>Fuentes encontradas:</strong> {news_gen.total_sources_found}<br>
                    <strong>Creado:</strong> {news_gen.created_at.strftime('%d/%m/%Y %H:%M')}
                </div>
                
                <div class="excerpt">
                    <strong>Extracto:</strong> {news_gen.generated_excerpt}
                </div>
                
                <div class="content">
                    {news_gen.generated_content}
                </div>
                
                <div class="sources">
                    <h3>Información de Generación ({len(news_gen.source_articles)})</h3>
            """
            
            for i, source in enumerate(news_gen.source_articles[:5], 1):
                if source.get('type', '').startswith('ai_'):
                    source_type_map = {
                        'ai_research': '📚 Investigación Técnica',
                        'ai_industry': '🏭 Reporte Industrial', 
                        'ai_academic': '🎓 Análisis Académico',
                        'ai_market': '📈 Tendencias de Mercado',
                        'ai_expert': '👥 Opiniones de Expertos'
                    }
                    
                    type_display = source_type_map.get(source.get('type', ''), '🤖 IA Especializada')
                    
                    html_preview += f"""
                        <div class="source-item">
                            <strong>{type_display}: {source.get('source_name', 'Fuente Especializada')}</strong><br>
                            <small><strong>Enfoque:</strong> {source.get('focus', 'N/A')}</small><br>
                            <small><strong>Descripción:</strong> {source.get('description', 'Análisis especializado generado por IA')}</small>
                        </div>
                    """
                elif source.get('type') == 'simulated':
                    html_preview += f"""
                        <div class="source-item">
                            <strong>🔧 Modo Desarrollo:</strong> {source.get('description', 'Contenido simulado')}<br>
                            <small>Modelo: {source.get('model', 'N/A')} | Fecha: {source.get('timestamp', 'N/A')}</small>
                        </div>
                    """
                else:
                    # Fallback para formato anterior
                    html_preview += f"""
                        <div class="source-item">
                            <strong>{i}. {source.get('title', source.get('source_name', 'Sin título'))}</strong><br>
                            <small>{source.get('description', '')}</small>
                        </div>
                    """
            
            html_preview += """
                </div>
            </body>
            </html>
            """
            
            from django.http import HttpResponse
            return HttpResponse(html_preview)
            
        except NewsGeneration.DoesNotExist:
            return HttpResponse("Generación no encontrada", status=404)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)
