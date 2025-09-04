import openai
from django.conf import settings
from django.utils import timezone
from decouple import config
from .models import NewsGeneration
import logging

logger = logging.getLogger(__name__)

class OpenAINewsGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config('OPENAI_API_KEY', default=''))
    
    def generate_news_article(self, tags):
        """
        Genera un artículo completo basándose en múltiples "fuentes simuladas"
        para crear contenido más rico y extenso
        """
        tags_text = ', '.join(tags)
        
        # Primero generar información de fuentes simuladas
        sources_info = self._generate_sources_context(tags_text)
        
        # Luego generar el artículo basado en esas fuentes
        article_content = self._generate_comprehensive_article(tags_text, sources_info)
        
        return article_content
    
    def _generate_sources_context(self, tags_text):
        """
        Genera contexto de múltiples fuentes simuladas para enriquecer el contenido
        """
        sources_prompt = f"""
        Actúa como un investigador que ha revisado múltiples fuentes especializadas sobre {tags_text}.
        
        Genera información de 5 fuentes diferentes que habrían cubierto aspectos relacionados con {tags_text}:
        
        Formato de respuesta (JSON):
        {{
            "sources": [
                {{
                    "name": "Nombre de publicación especializada",
                    "type": "Tipo de fuente (revista, blog, periódico, etc.)",
                    "focus": "Enfoque específico de esta fuente sobre el tema",
                    "key_points": ["punto clave 1", "punto clave 2", "punto clave 3"]
                }}
            ]
        }}
        
        REQUISITOS:
        - Exactamente 5 fuentes diferentes
        - Cada fuente debe tener un enfoque único
        - Los puntos clave deben ser específicos y detallados
        - Las fuentes deben ser creíbles para el tema {tags_text}
        
        Tema: {tags_text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": sources_prompt}],
                max_tokens=1500,
                temperature=0.8
            )
            
            import json
            sources_data = json.loads(response.choices[0].message.content.strip())
            return sources_data.get('sources', [])
            
        except Exception as e:
            logger.warning(f"Error generando fuentes: {e}")
            return self._generate_default_sources(tags_text)
    
    def _generate_default_sources(self, tags_text):
        """
        Genera fuentes por defecto si falla la generación automática
        """
        return [
            {
                "name": f"Tech {tags_text.split(',')[0].strip().title()} Review",
                "type": "revista especializada",
                "focus": f"Análisis técnico de {tags_text}",
                "key_points": [f"Tendencias en {tags_text}", "Impacto en la industria", "Perspectivas futuras"]
            },
            {
                "name": "Innovation Daily",
                "type": "periódico digital", 
                "focus": f"Innovaciones recientes en {tags_text}",
                "key_points": ["Desarrollos recientes", "Casos de éxito", "Desafíos actuales"]
            }
        ]
    
    def _generate_comprehensive_article(self, tags_text, sources):
        """
        Genera un artículo extenso basado en múltiples fuentes
        """
        sources_context = ""
        for i, source in enumerate(sources[:5], 1):
            sources_context += f"\nFuente {i} - {source['name']} ({source['type']}):\n"
            sources_context += f"Enfoque: {source['focus']}\n"
            sources_context += f"Puntos clave: {', '.join(source['key_points'])}\n"
        
        comprehensive_prompt = f"""
        Eres un periodista senior escribiendo un artículo de investigación sobre {tags_text}.
        
        Has consultado múltiples fuentes especializadas:
        {sources_context}
        
        REQUISITOS DEL ARTÍCULO:
        - MÍNIMO 800 palabras (muy importante)
        - MÍNIMO 6 párrafos principales
        - Incluir al menos 3 subtítulos <h3>
        - Estructura profesional: introducción, desarrollo (múltiples secciones), conclusión
        - Mencionar diferentes perspectivas basadas en las fuentes
        - Incluir datos específicos y ejemplos concretos
        - Tono profesional y periodístico
        
        ESTRUCTURA REQUERIDA:
        1. Introducción (2 párrafos)
        2. Desarrollo principal (4-5 párrafos con subtítulos)
        3. Análisis de impacto (2 párrafos)
        4. Perspectivas futuras (2 párrafos)
        5. Conclusión (1 párrafo)
        
        Respuesta en formato JSON:
        {{
            "title": "Título impactante (máximo 65 caracteres)",
            "excerpt": "Resumen ejecutivo del artículo (200-250 caracteres)",
            "content": "Artículo completo en HTML con estructura profesional",
            "meta_description": "Descripción SEO optimizada (150-160 caracteres)",
            "meta_keywords": "15-20 palabras clave relevantes separadas por comas",
            "word_count": "número aproximado de palabras del contenido"
        }}
        
        IMPORTANTE: El contenido debe ser sustancioso, informativo y parecer escrito por un experto en {tags_text}.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": comprehensive_prompt}],
                max_tokens=3000,  # Aumentado para contenido más extenso
                temperature=0.6
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            
            # Validar longitud mínima
            content_length = len(result.get('content', ''))
            if content_length < 2000:  # Mínimo de caracteres
                logger.warning(f"Contenido generado muy corto ({content_length} chars), regenerando...")
                return self._generate_extended_content(tags_text, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando artículo comprensivo: {e}")
            return self._generate_fallback_content(tags_text, str(e))
    
    def _generate_extended_content(self, tags_text, base_result):
        """
        Extiende el contenido si es muy corto
        """
        extension_prompt = f"""
        El siguiente artículo sobre {tags_text} necesita ser expandido significativamente:

        Título actual: {base_result.get('title', '')}
        Contenido actual: {base_result.get('content', '')}
        
        TAREA: Expandir el contenido a MÍNIMO 800 palabras, agregando:
        - Más ejemplos específicos y casos de estudio
        - Análisis más profundo de las implicaciones
        - Comparaciones con situaciones similares
        - Datos y estadísticas relevantes
        - Perspectivas de diferentes stakeholders
        - Secciones adicionales con subtítulos <h3>
        
        Mantén el título original pero expande dramáticamente el contenido.
        
        Responde en JSON:
        {{
            "title": "{base_result.get('title', f'Análisis Completo: {tags_text.title()}')}",
            "content": "contenido expandido sustancialmente",
            "excerpt": "resumen actualizado",
            "meta_description": "descripción actualizada",
            "meta_keywords": "{tags_text}, análisis, tendencias, innovación, tecnología, futuro"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": extension_prompt}],
                max_tokens=3500,
                temperature=0.6
            )
            
            import json
            extended_result = json.loads(response.choices[0].message.content.strip())
            return extended_result
            
        except Exception as e:
            logger.error(f"Error extendiendo contenido: {e}")
            return base_result  # Devolver el contenido original si falla
    
    def _generate_fallback_content(self, tags_text, raw_content):
        """
        Genera contenido estructurado cuando falla el parseo JSON
        """
        return {
            'title': f'Últimas Noticias: {tags_text.title()}',
            'excerpt': f'Análisis de las tendencias más recientes en {tags_text}.',
            'content': f'<p>Desarrollos importantes en el campo de <strong>{tags_text}</strong>.</p><p>{raw_content[:500]}...</p>',
            'meta_description': f'Noticias actualizadas sobre {tags_text}.',
            'meta_keywords': f'{tags_text}, noticias, actualidad, tendencias'
        }


class SimpleNewsGenerationService:
    def __init__(self):
        self.ai_generator = OpenAINewsGenerator()
    
    def process_news_generation(self, news_generation_id):
        """
        Procesa una generación de noticias usando únicamente OpenAI
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_generation_id)
            
            # Actualizar estado a buscando fuentes
            news_gen.status = 'SEARCHING'
            news_gen.save()
            
            logger.info(f"Simulando búsqueda de fuentes para tags: {news_gen.tags}")
            
            # Actualizar a generando contenido
            news_gen.status = 'GENERATING'
            news_gen.save()
            
            logger.info(f"Generando contenido IA comprensivo para tags: {news_gen.tags}")
            
            # Generar contenido directamente con OpenAI (ahora con múltiples fuentes simuladas)
            generated = self.ai_generator.generate_news_article(news_gen.tags_list)
            
            # Actualizar modelo con contenido generado
            news_gen.generated_title = generated['title']
            news_gen.generated_content = generated['content']
            news_gen.generated_excerpt = generated['excerpt']
            news_gen.generated_meta_description = generated['meta_description']
            news_gen.generated_meta_keywords = generated['meta_keywords']
            
            # Simular múltiples fuentes especializadas
            simulated_sources = [
                {
                    'type': 'ai_research',
                    'source_name': f'Tech Research {news_gen.tags_list[0].title()} Journal',
                    'focus': f'Análisis técnico de {news_gen.tags_list[0]}',
                    'description': f'Investigación especializada en tendencias de {news_gen.tags_list[0]}'
                },
                {
                    'type': 'ai_industry',  
                    'source_name': 'Industry Innovation Report',
                    'focus': f'Impacto industrial de {", ".join(news_gen.tags_list[:2])}',
                    'description': f'Reporte de industria sobre innovaciones en {", ".join(news_gen.tags_list[:2])}'
                },
                {
                    'type': 'ai_academic',
                    'source_name': f'{news_gen.tags_list[0].title()} Academic Review',
                    'focus': f'Perspectiva académica sobre {news_gen.tags_list[0]}',
                    'description': f'Análisis académico de desarrollos en {news_gen.tags_list[0]}'
                },
                {
                    'type': 'ai_market',
                    'source_name': 'Market Trends Analysis',
                    'focus': f'Tendencias de mercado en {", ".join(news_gen.tags_list)}',
                    'description': f'Análisis de mercado y proyecciones para {", ".join(news_gen.tags_list)}'
                },
                {
                    'type': 'ai_expert',
                    'source_name': 'Expert Opinion Network',
                    'focus': f'Opiniones de expertos sobre {", ".join(news_gen.tags_list)}',
                    'description': f'Compilación de opiniones expertas en {", ".join(news_gen.tags_list)}'
                }
            ]
            
            news_gen.source_articles = simulated_sources
            news_gen.total_sources_found = len(simulated_sources)
            
            news_gen.status = 'COMPLETED'
            news_gen.completed_at = timezone.now()
            news_gen.save()
            
            logger.info(f"Generación completada exitosamente para ID {news_generation_id}")
            return news_gen
            
        except Exception as e:
            logger.error(f"Error procesando generación {news_generation_id}: {e}")
            
            try:
                news_gen = NewsGeneration.objects.get(id=news_generation_id)
                news_gen.status = 'ERROR'
                news_gen.error_message = str(e)
                news_gen.save()
            except:
                pass
            
            raise


# Versión de desarrollo que simula OpenAI sin usar la API real
class MockSimpleNewsGenerationService:
    def process_news_generation(self, news_generation_id):
        """
        Simula la generación para desarrollo
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_generation_id)
            
            news_gen.status = 'GENERATING'
            news_gen.save()
            
            # Simular procesamiento
            import time
            time.sleep(1)
            
            tags_str = ', '.join(news_gen.tags_list)
            
            # Contenido simulado pero realista
            mock_content = f"""
            <p>En los últimos desarrollos relacionados con <strong>{tags_str}</strong>, se han identificado tendencias significativas que están transformando el panorama actual del sector.</p>
            
            <h3>Avances Principales</h3>
            <p>Los expertos en {tags_str} reportan cambios sustanciales que prometen redefinir las expectativas de la industria en los próximos meses.</p>
            
            <p>Estos desarrollos representan un punto de inflexión importante, con implicaciones que van más allá de lo que inicialmente se anticipaba en el campo de {tags_str}.</p>
            
            <h3>Impacto y Perspectivas</h3>
            <p>El impacto de estas innovaciones se extiende a múltiples sectores, creando nuevas oportunidades y desafíos para los profesionales del área.</p>
            
            <p>Los analistas sugieren que estamos ante el inicio de una nueva era en {tags_str}, con potencial para generar cambios duraderos en la forma en que operan las organizaciones del sector.</p>
            
            <p><em>Este análisis se basa en las últimas tendencias identificadas en el campo de {tags_str}.</em></p>
            """
            
            # Actualizar con contenido simulado
            news_gen.generated_title = f'Nuevos Desarrollos Transforman {tags_str.title()}'
            news_gen.generated_content = mock_content
            news_gen.generated_excerpt = f'Análisis de las últimas tendencias en {tags_str} que están redefiniendo el sector.'
            news_gen.generated_meta_description = f'Descubre los últimos avances en {tags_str} y su impacto en la industria.'
            news_gen.generated_meta_keywords = f'{tags_str}, innovación, tendencias, análisis, noticias'
            
            news_gen.source_articles = [{
                'type': 'simulated',
                'description': f'Contenido simulado para desarrollo - tema: {news_gen.tags}',
                'model': 'mock-ai',
                'timestamp': timezone.now().isoformat()
            }]
            news_gen.total_sources_found = 1
            
            news_gen.status = 'COMPLETED'
            news_gen.completed_at = timezone.now()
            news_gen.save()
            
            logger.info(f"[MODO DEV] Generación simulada completada para ID {news_generation_id}")
            return news_gen
            
        except Exception as e:
            logger.error(f"[MODO DEV] Error: {e}")
            
            try:
                news_gen = NewsGeneration.objects.get(id=news_generation_id)
                news_gen.status = 'ERROR'
                news_gen.error_message = f"[DEV] {str(e)}"
                news_gen.save()
            except:
                pass
                
            raise