import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import re
import warnings

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


def get_youtube_id(url):
    """Extrai o ID do vídeo de várias URLs do YouTube."""
    if not url:
        return None
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|shorts\/|youtu.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_source_url(html_content):
    """Extrai a primeira URL 'principal' de um bloco de HTML (de um iframe ou link)."""
    if not html_content:
        return ''
    soup = BeautifulSoup(html_content, 'html.parser')

    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if 'instagram.com' in src:
            return src.replace('/embed', '').split('?')[0]
        return src

    og_link = soup.find('a')
    if og_link and og_link.get('href'):
        return og_link['href']

    # Se for apenas texto com um link, extrai o link
    url_match = re.search(r'https?:\/\/[^\s"]+', html_content)
    if url_match:
        return url_match.group(0)

    return ''


def generate_embed_data(url):
    """
    Analisa uma URL e retorna dados estruturados para criar um embed ou um cartão de preview.
    """
    if not url:
        return None
    # --- REGISTRO DE PROVEDORES ---

    youtube_id = get_youtube_id(url)
    if youtube_id:
        return {
            'type': 'iframe', 'ratio': 'aspect-video',
            'html': f'<iframe src="https://www.youtube-nocookie.com/embed/{youtube_id}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen sandbox="allow-scripts allow-same-origin allow-presentation allow-popups" referrerpolicy="strict-origin-when-cross-origin"></iframe>'
        }

    if 'instagram.com/' in url:
        # Garante que a URL termine com uma barra para a incorporação funcionar bem
        clean_url = url.split('?')[0]
        if not clean_url.endswith('/'):
            clean_url += '/'
        return {
            'type': 'iframe', 'ratio': 'aspect-square',
            'html': f'<iframe src="{clean_url}embed" loading="lazy" allowtransparency="true" scrolling="no" sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"></iframe>'
        }

    if 'drive.google.com/' in url or 'docs.google.com/' in url:
        preview_url = url.replace(
            '/view', '/preview').replace('/edit', '/preview')
        return {
            'type': 'iframe', 'ratio': 'aspect-document',
            'html': f'<iframe src="{preview_url}" loading="lazy" allow="autoplay" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>'
        }

    # --- FALLBACK PARA OPEN GRAPH (OG) CARD ---
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=5, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        og_title = soup.find('meta', property='og:title')
        og_image = soup.find('meta', property='og:image')

        if og_title and og_image:
            og_description = soup.find('meta', property='og:description')
            og_site_name = soup.find('meta', property='og:site_name')
            return {
                'type': 'og-card', 'ratio': 'aspect-og',
                'data': {
                    'url': url,
                    'title': og_title['content'],
                    'description': og_description['content'] if og_description else '',
                    'image': og_image['content'],
                    'site_name': og_site_name['content'] if og_site_name else url.split('/')[2],
                }
            }
    except requests.RequestException:
        pass

    return None
