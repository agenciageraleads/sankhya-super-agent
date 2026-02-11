import sqlite3
import os
import logging
from typing import List, Dict

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("knowledge-indexer")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server", "knowledge.db")

# Artigos "Seed" para popular a KB inicial
# Focados em erros comuns do Resilience Lab e do dia-a-dia Sankhya
INITIAL_ARTICLES = [
    {
        "title": "Erro: Nenhum provedor foi encontrado para o serviço (HttpServiceBroker)",
        "body": """
        **Problema:** Ao chamar um serviço via API, retorna "HttpServiceBroker: Nenhum provedor foi encontrado para o serviço 'NomeDoServico'".
        
        **Tags:** HttpServiceBroker, provedor, serviço, ServiceName, encontrado.
        
        **Causa:**
        1. O nome do serviço está incorreto (typo).
        2. O serviço não está implantado ou ativo nesta versão do Sankhya.
        3. O usuário não tem permissão de acesso a este serviço (ACESSOS).

        **Solução:**
        - Verifique a grafia exata do `serviceName`.
        - Consulte a tela "Especializações de Serviço" no Sankhya W para ver se o serviço existe.
        """,
        "url": "https://ajuda.sankhya.com.br/artigo/erro-servico-nao-encontrado"
    },
    {
        "title": "Erro de Validação: Preencha o campo referente ao...",
        "body": """
        **Problema:** Ao tentar salvar (saveRecord) uma entidade, retorna "Por favor, preencha o campo referente ao...".
        
        **Tags:** preencha, campo, referente, obrigatório, nulo, required.
        
        **Causa:**
        - Você está tentando inserir um registro sem informar um campo obrigatório (NOT NULL) no banco ou no Dicionário de Dados.
        
        **Solução:**
        - Consulte a estrutura da tabela (`get_table_columns`) para ver quais campos são obrigatórios.
        - Para a entidade `Usuario`, o campo `NOMEUSU` é obrigatório.
        """,
        "url": "https://ajuda.sankhya.com.br/artigo/erro-campos-obrigatorios"
    },
    {
        "title": "Rejeição 997: Série já vinculada a outra inscrição estadual",
        "body": """
        **Problema:** Ao confirmar nota fiscal, ocorre a Rejeição 997 da SEFAZ.
        
        **Causa:**
        - A Série utilizada na nota já foi utilizada anteriormente por outra Filial (CNPJ) do mesmo grupo econômico, o que bloqueia o uso cruzado.
        
        **Solução:**
        1. Acesse a tela "Controle de Numeração" (TGFNUM).
        2. Verifique qual a próxima numeração livre para a Série/Modelo.
        3. Se necessário, crie uma NOVA Série exclusiva para esta Filial.
        4. Inutilize a numeração problemática se houve salto.
        """,
        "url": "https://ajuda.sankhya.com.br/artigo/rejeicao-997-serie-vinculada"
    },
    {
        "title": "Rejeição: Total da Nota difere do somatório dos itens",
        "body": """
        **Problema:** Erro de validação de totais na NF-e.
        
        **Causa:**
        - A soma dos valores dos itens (vProd) + impostos + frete - descontos não bate com o vNF no cabeçalho.
        - Problema comum de arredondamento (2 casas decimais).

        **Solução:**
        - Recalcule os itens e verifique diferenças de centavos.
        - Use a função de "Recalcular Impostos" no Portal de Vendas.
        - Verifique se algum item tem desconto maior que o total.
        """,
        "url": "https://ajuda.sankhya.com.br/artigo/rejeicao-total-nota-difere"
    },
    {
        "title": "Erro ORA-00942: a tabela ou view não existe",
        "body": """
        **Problema:** Erro de banco de dados Oracle ao executar query SQL.
        
        **Causa:**
        1. O nome da tabela está errado.
        2. O usuário do banco não tem GRANT de select na tabela.
        3. A tabela pertence a outro schema e precisa de prefixo (ex: SANKHYA.TGFCAB).

        **Solução:**
        - Use a ferramenta `list_tables` ou `search_docs` para confirmar o nome da tabela.
        - Tabelas comuns: TGFCAB (Notas), TGFITE (Itens), TGFPAR (Parceiros), TGFPRO (Produtos).
        """,
        "url": "https://ajuda.sankhya.com.br/artigo/ora-00942-tabela-nao-existe"
    }
]

def init_db():
    dir_path = os.path.dirname(DB_PATH)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Cria tabela principal de artigos
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            url TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Cria tabela virtual FTS5 para busca textual full-text eficiente
    # Se der erro (versão antiga do SQLite), faremos fallback para LIKE
    try:
        c.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts 
            USING fts5(title, body, content='articles', content_rowid='id')
        ''')
        logger.info("✅ Tabela FTS5 criada com sucesso.")
    except Exception as e:
        logger.warning(f"⚠️ FTS5 não suportado, busca será lenta: {e}")

    conn.commit()
    conn.close()

def index_article(article: Dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Verifica duplicidade por título
    c.execute("SELECT id FROM articles WHERE title = ?", (article["title"],))
    if c.fetchone():
        logger.info(f"Artigo já existe: {article['title']}")
        conn.close()
        return

    # Insere no banco principal
    c.execute("""
        INSERT INTO articles (title, body, url) VALUES (?, ?, ?)
    """, (article["title"], article["body"], article["url"]))
    
    # Pega o ID inserido
    row_id = c.lastrowid
    
    # Insere no índice FTS
    try:
        c.execute("""
            INSERT INTO articles_fts (rowid, title, body) VALUES (?, ?, ?)
        """, (row_id, article["title"], article["body"]))
    except:
        pass
        
    conn.commit()
    conn.close()
    logger.info(f"➕ Artigo indexado: {article['title']}")

def populate_kb():
    logger.info("🚀 Iniciando população da Knowledge Base...")
    init_db()
    
    for art in INITIAL_ARTICLES:
        index_article(art)
        
    logger.info(f"✅ KB populada com {len(INITIAL_ARTICLES)} artigos iniciais.")

if __name__ == "__main__":
    populate_kb()
