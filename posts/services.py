import requests
import openai
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from decouple import config
from .models import NewsGeneration
import logging

logger = logging.getLogger(__name__)

class NewsSearchService:
    def __init__(self):
        self.news_api_key = config('NEWS_API_KEY', default='')
        self.news_api_url = 'https://newsapi.org/v2/everything'
    
    def search_news(self, tags, max_articles=10, language='es', sort_by='publishedAt'):
        """
        Busca noticias usando NewsAPI basado en los tags proporcionados
        """
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY no configurada")
        
        # Construir query de búsqueda
        query = ' OR '.join(tags)
        
        params = {
            'q': query,
            'apiKey': self.news_api_key,
            'language': language,
            'sortBy': sort_by,
            'pageSize': max_articles,
            'excludeDomains': 'youtube.com,facebook.com,twitter.com,instagram.com'  # Excluir redes sociales
        }
        
        try:
            response = requests.get(self.news_api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'ok':
                raise Exception(f"Error en NewsAPI: {data.get('message', 'Unknown error')}")
            
            articles = []
            for article in data.get('articles', []):
                # Filtrar artículos sin contenido
                if not article.get('title') or not article.get('description'):
                    continue
                
                articles.append({
                    'title': article['title'],
                    'description': article['description'], 
                    'url': article['url'],
                    'published_at': article['publishedAt'],
                    'source': article['source']['name'],
                    'author': article.get('author', ''),
                    'url_to_image': article.get('urlToImage', ''),
                    'content': self._extract_full_content(article['url'])
                })
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al buscar noticias: {e}")
            raise Exception(f"Error de conexión con NewsAPI: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise
    
    def _extract_full_content(self, url):
        """
        Extrae el contenido completo del artículo desde la URL
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remover elementos no deseados
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Buscar el contenido principal
            content = ""
            
            # Intentar diferentes selectores comunes para contenido
            selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                'main',
                '.story-body'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    # Extraer solo párrafos de texto
                    paragraphs = element.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(content) > 200:  # Contenido suficiente
                        break
            
            # Fallback: buscar todos los párrafos
            if len(content) < 200:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return content[:2000]  # Limitar contenido
            
        except Exception as e:
            logger.warning(f"No se pudo extraer contenido de {url}: {e}")
            return ""


class AIContentGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config('OPENAI_API_KEY', default=''))
    
    def generate_news_article(self, source_articles, tags):
        """
        Genera un artículo compilado basado en los artículos fuente
        """
        if not source_articles:
            raise ValueError("No hay artículos fuente para generar contenido")
        
        # Preparar contexto para la IA
        sources_text = self._prepare_sources_context(source_articles)
        tags_text = ', '.join(tags)
        
        # Generar título
        title = self._generate_title(sources_text, tags_text)
        
        # Generar contenido
        content = self._generate_content(sources_text, tags_text, title)
        
        # Generar extracto
        excerpt = self._generate_excerpt(content)
        
        # Generar meta description
        meta_description = self._generate_meta_description(title, excerpt)
        
        # Generar keywords
        meta_keywords = self._generate_keywords(tags_text, content)
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'meta_description': meta_description,
            'meta_keywords': meta_keywords
        }
    
    def _prepare_sources_context(self, articles):
        """
        Prepara el contexto de los artículos fuente para la IA
        """
        context = "Artículos de referencia:\n\n"
        
        for i, article in enumerate(articles[:5], 1):  # Máximo 5 artículos
            context += f"{i}. **{article['title']}** ({article['source']})\n"
            context += f"   Descripción: {article['description']}\n"
            if article.get('content'):
                context += f"   Contenido: {article['content'][:500]}...\n"
            context += f"   URL: {article['url']}\n\n"
        
        return context
    
    def _generate_title(self, sources_text, tags_text):
        """
        Genera un título atractivo para el artículo compilado
        """
        prompt = f"""
        Basándote en estos artículos sobre {tags_text}, genera un título atractivo y informativo en español para un nuevo artículo que compile la información más relevante.

        {sources_text}

        Requisitos:
        - Máximo 60 caracteres
        - Debe ser llamativo pero profesional
        - En español
        - Que capture la esencia de la información más importante
        
        Responde solo con el título, sin comillas ni explicaciones.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generando título: {e}")
            return f"Últimas noticias sobre {tags_text}"
    
    def _generate_content(self, sources_text, tags_text, title):
        """
        Genera el contenido principal del artículo en HTML
        """
        prompt = f"""
        Eres un periodista profesional. Crea un artículo completo en español basándote en las siguientes fuentes sobre {tags_text}.

        {sources_text}

        Título del artículo: {title}

        Instrucciones:
        1. Escribe un artículo periodístico profesional de 400-600 palabras
        2. Utiliza formato HTML simple (<p>, <h3>, <strong>, <em>)
        3. Incluye subtítulos cuando sea apropiado
        4. Combina información de múltiples fuentes sin plagiar
        5. Mantén un tono profesional e informativo
        6. No incluyas enlaces externos
        7. No menciones las fuentes directamente en el texto
        8. El artículo debe fluir naturalmente y ser original

        Responde solo con el contenido HTML, sin explicaciones adicionales.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generando contenido: {e}")
            return f"<p>Error al generar contenido automático sobre {tags_text}.</p>"
    
    def _generate_excerpt(self, content):
        """
        Genera un extracto a partir del contenido
        """
        # Extraer texto limpio del HTML
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Tomar las primeras frases hasta 250 caracteres
        sentences = text.split('.')[:3]
        excerpt = '. '.join(sentences).strip()
        
        if len(excerpt) > 250:
            excerpt = excerpt[:250] + "..."
        
        return excerpt
    
    def _generate_meta_description(self, title, excerpt):
        """
        Genera meta description para SEO
        """
        meta_desc = excerpt[:160]
        if len(excerpt) > 160:
            meta_desc = meta_desc.rsplit(' ', 1)[0] + "..."
        
        return meta_desc
    
    def _generate_keywords(self, tags_text, content):
        """
        Genera keywords para SEO
        """
        # Combinar tags originales con keywords extraídas del contenido
        keywords = tags_text
        
        # Agregar algunas palabras clave generales
        general_keywords = ["noticias", "actualidad", "información"]
        all_keywords = keywords + ", " + ", ".join(general_keywords)
        
        return all_keywords[:255]  # Limitar a 255 caracteres


class NewsGenerationService:
    def __init__(self):
        self.news_search = NewsSearchService()
        self.ai_generator = AIContentGenerator()
    
    def process_news_generation(self, news_generation_id):
        """
        Procesa una generación de noticias completa: busca, analiza y genera contenido
        """
        try:
            news_gen = NewsGeneration.objects.get(id=news_generation_id)
            
            # Actualizar estado
            news_gen.status = 'SEARCHING'
            news_gen.save()
            
            # Buscar noticias
            logger.info(f"Buscando noticias para tags: {news_gen.tags}")
            articles = self.news_search.search_news(news_gen.tags_list)
            
            news_gen.source_articles = articles
            news_gen.total_sources_found = len(articles)
            news_gen.status = 'GENERATING'
            news_gen.save()
            
            if not articles:
                raise Exception("No se encontraron artículos para los tags especificados")
            
            # Generar contenido con IA
            logger.info(f"Generando contenido con IA para {len(articles)} artículos")
            generated = self.ai_generator.generate_news_article(articles, news_gen.tags_list)
            
            # Actualizar modelo con contenido generado
            news_gen.generated_title = generated['title']
            news_gen.generated_content = generated['content']
            news_gen.generated_excerpt = generated['excerpt']
            news_gen.generated_meta_description = generated['meta_description']
            news_gen.generated_meta_keywords = generated['meta_keywords']
            news_gen.status = 'COMPLETED'
            news_gen.completed_at = timezone.now()
            news_gen.save()
            
            logger.info(f"Generación completada para ID {news_generation_id}")
            return news_gen
            
        except Exception as e:
            logger.error(f"Error procesando generación {news_generation_id}: {e}")
            
            news_gen.status = 'ERROR'
            news_gen.error_message = str(e)
            news_gen.save()
            
            raise