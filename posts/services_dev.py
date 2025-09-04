"""
Versión de desarrollo de los servicios - simula respuestas de IA sin usar OpenAI
Útil para probar el sistema mientras se configura la cuenta de OpenAI
"""
import time
from .services import NewsSearchService as BaseNewsSearchService, NewsGenerationService as BaseNewsGenerationService
from .models import NewsGeneration
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MockAIContentGenerator:
    """
    Generador de contenido simulado para desarrollo
    """
    
    def generate_news_article(self, source_articles, tags):
        """
        Simula la generación de un artículo con contenido de ejemplo
        """
        time.sleep(2)  # Simular procesamiento
        
        tags_str = ', '.join(tags)
        
        # Contenido simulado pero realista
        mock_content = f"""
        <p>En un desarrollo significativo en el campo de <strong>{tags_str}</strong>, múltiples fuentes reportan avances importantes que podrían transformar el panorama actual de la industria.</p>
        
        <h3>Desarrollos Recientes</h3>
        <p>Los últimos reportes indican tendencias emergentes que están captando la atención de expertos en el sector. Estos cambios representan una evolución natural en el ámbito de {tags_str}.</p>
        
        <p>Las implicaciones de estos desarrollos se extienden más allá de las expectativas iniciales, sugiriendo un impacto duradero en múltiples sectores relacionados.</p>
        
        <h3>Perspectivas Futuras</h3>
        <p>Los analistas sugieren que estos avances marcan el inicio de una nueva fase en {tags_str}, con potencial para generar cambios significativos en los próximos meses.</p>
        
        <p><em>Este artículo fue generado automáticamente a partir de múltiples fuentes de información actualizadas.</em></p>
        """
        
        return {
            'title': f'Últimas Tendencias en {tags_str.title()}',
            'content': mock_content,
            'excerpt': f'Análisis de los desarrollos más recientes en {tags_str}, basado en múltiples fuentes de información actualizadas.',
            'meta_description': f'Descubre las últimas tendencias y desarrollos en {tags_str}. Análisis completo basado en fuentes actualizadas.',
            'meta_keywords': f'{tags_str}, noticias, actualidad, tendencias, análisis'
        }

class DevNewsGenerationService(BaseNewsGenerationService):
    """
    Servicio de generación en modo desarrollo - usa contenido simulado
    """
    
    def __init__(self):
        self.news_search = BaseNewsSearchService()
        self.ai_generator = MockAIContentGenerator()  # Usar mock en lugar del real
    
    def process_news_generation(self, news_generation_id):
        """
        Procesa generación usando fuentes reales pero IA simulada
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_generation_id)
            
            # Actualizar estado
            news_gen.status = 'SEARCHING'
            news_gen.save()
            
            logger.info(f"[DEV MODE] Simulando búsqueda para tags: {news_gen.tags}")
            
            # Para desarrollo, crear artículos simulados en lugar de usar API real
            articles = self._create_mock_articles(news_gen.tags_list)
            
            news_gen.source_articles = articles
            news_gen.total_sources_found = len(articles)
            news_gen.status = 'GENERATING'
            news_gen.save()
            
            # Generar contenido con IA simulada
            logger.info(f"[DEV MODE] Generando contenido simulado")
            generated = self.ai_generator.generate_news_article(articles, news_gen.tags_list)
            
            # Actualizar modelo
            news_gen.generated_title = generated['title']
            news_gen.generated_content = generated['content']
            news_gen.generated_excerpt = generated['excerpt']
            news_gen.generated_meta_description = generated['meta_description']
            news_gen.generated_meta_keywords = generated['meta_keywords']
            news_gen.status = 'COMPLETED'
            news_gen.completed_at = timezone.now()
            news_gen.save()
            
            logger.info(f"[DEV MODE] Generación completada para ID {news_generation_id}")
            return news_gen
            
        except Exception as e:
            logger.error(f"[DEV MODE] Error procesando generación {news_generation_id}: {e}")
            
            news_gen.status = 'ERROR'
            news_gen.error_message = f"[DEV MODE] {str(e)}"
            news_gen.save()
            
            raise
    
    def _create_mock_articles(self, tags):
        """
        Crea artículos simulados basados en los tags
        """
        mock_articles = []
        
        for i, tag in enumerate(tags[:3], 1):  # Máximo 3 artículos simulados
            mock_articles.append({
                'title': f'Desarrollo #{i} en {tag.title()}',
                'description': f'Nuevos avances reportados en el campo de {tag}, según fuentes especializadas.',
                'url': f'https://ejemplo.com/noticia-{i}-{tag.replace(" ", "-")}',
                'published_at': '2024-01-15T10:30:00Z',
                'source': f'Source{i}',
                'author': f'Reportero {i}',
                'url_to_image': '',
                'content': f'Contenido detallado sobre {tag}. Este es un artículo simulado para propósitos de desarrollo y prueba del sistema de generación automática de noticias.'
            })
        
        return mock_articles