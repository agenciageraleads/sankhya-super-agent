import os
import requests
import sqlite3
import logging
import re
from datetime import datetime
from typing import List, Dict, Any

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("knowledge-indexer")

# Configuração
ZENDESK_API_URL = "https://ajuda.sankhya.com.br/api/v2/help_center/articles.json"
DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")

def create_database():
    """Cria o banco de dados SQLite com suporte a FTS5 (Full-Text Search)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela principal de artigos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY,
        url TEXT,
        title TEXT,
        body TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    # Tabela virtual FTS5 para busca textual eficiente
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
        title, 
        body, 
        content='articles', 
        content_rowid='id'
    )
    """)
    
    # Triggers para manter o índice FTS sincronizado
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
      INSERT INTO articles_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
      INSERT INTO articles_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
    END;
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Banco de dados inicializado em {DB_PATH}")

def clean_html(raw_html: str) -> str:
    """Remove tags HTML e limpa o texto para indexação."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, ' ', raw_html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_articles() -> List[Dict[str, Any]]:
    """Baixa todos os artigos da API do Zendesk (paginado)."""
    articles = []
    url = ZENDESK_API_URL
    page = 1
    
    while url:
        logger.info(f"Baixando página {page}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 429: # Rate limit
                 logger.warning("Rate limit atingido. Aguardando...")
                 import time
                 time.sleep(10)
                 continue
            
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("articles", []):
                # Apenas artigos publicados e em português (assumindo que a URL base já filtra locale, mas garantindo)
                if not item.get("draft") and item.get("locale") == "pt-br": 
                    articles.append({
                        "id": item["id"],
                        "url": item["html_url"],
                        "title": item["title"],
                        "body": clean_html(item["body"]), # Limpa HTML antes de salvar
                        "created_at": item["created_at"],
                        "updated_at": item["updated_at"]
                    })
            
            url = data.get("next_page")
            page += 1
            
        except Exception as e:
            logger.error(f"Erro ao baixar página {page}: {e}")
            break
            
    return articles

def index_articles(articles: List[Dict[str, Any]]):
    """Salva os artigos no banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count_new = 0
    count_updated = 0
    
    for art in articles:
        try:
            # Verifica se já existe
            cursor.execute("SELECT updated_at FROM articles WHERE id = ?", (art["id"],))
            row = cursor.fetchone()
            
            if row:
                if row[0] != art["updated_at"]:
                    # Atualiza se mudou
                    cursor.execute("""
                        UPDATE articles 
                        SET url=?, title=?, body=?, updated_at=? 
                        WHERE id=?
                    """, (art["url"], art["title"], art["body"], art["updated_at"], art["id"]))
                    count_updated += 1
            else:
                # Insere novo
                cursor.execute("""
                    INSERT INTO articles (id, url, title, body, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (art["id"], art["url"], art["title"], art["body"], art["created_at"], art["updated_at"]))
                count_new += 1
                
        except Exception as e:
            logger.error(f"Erro ao indexar artigo {art['id']}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"Indexação concluída: {count_new} novos, {count_updated} atualizados.")

if __name__ == "__main__":
    logger.info("Iniciando indexador de Knowledge Base Sankhya...")
    create_database()
    articles = fetch_articles()
    logger.info(f"Total de {len(articles)} artigos baixados. Indexando...")
    index_articles(articles)
    logger.info("Processo finalizado com sucesso.")
