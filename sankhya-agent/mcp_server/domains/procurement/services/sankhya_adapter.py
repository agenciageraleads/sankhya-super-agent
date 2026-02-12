import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from mcp_server.utils import sankhya

logger = logging.getLogger("procurement-sankhya-service")

class SankhyaProcurementService:
    """
    Serviço especializado para extração de dados do domínio de Compras.
    Utiliza as queries customizadas e aplica a camada de abstração.
    """

    def __init__(self, domain_path: str):
        self.domain_path = domain_path
        self.rules_path = os.path.join(domain_path, "rules")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_file = os.path.join(self.rules_path, "business_rules.yaml")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _read_sql(self, filename: str) -> str:
        filepath = os.path.join(self.rules_path, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _execute_with_params(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Substitui parâmetros nominais :PARAM por valores reais e executa."""
        processed_sql = sql
        for key, value in params.items():
            placeholder = f":{key}"
            if value is None:
                processed_sql = processed_sql.replace(placeholder, "NULL")
            elif isinstance(value, str):
                # SQL Oracle básico: escapa aspas
                safe_value = value.replace("'", "''")
                processed_sql = processed_sql.replace(placeholder, f"'{safe_value}'")
            else:
                processed_sql = processed_sql.replace(placeholder, str(value))
        
        try:
            return sankhya.execute_query(processed_sql)
        except Exception as e:
            logger.error(f"Erro ao executar query com parâmetros: {e}")
            logger.debug(f"SQL Processado: {processed_sql}")
            return []

    def get_abc_giro_data(self) -> List[Dict[str, Any]]:
        """Busca dados da tabela de Giro / Curva ABC."""
        sql = self._read_sql("queries_abc.sql")
        if not sql or "SELECT 0 FROM DUAL" in sql:
            logger.warning("Query de ABC/Giro não configurada ou placeholder detectado.")
            return []
        
        try:
            return sankhya.execute_query(sql)
        except Exception as e:
            logger.error(f"Erro ao buscar dados de ABC/Giro: {e}")
            return []

    # Skill 1: Popularidade e Demanda Reprimida (Summary)
    def get_popularity_analysis(self, ini: str, fin: str, empresa: Optional[str] = None, codprod: Optional[int] = None, grupoprod: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Skill: Análise de Popularidade e Perda de Vendas.
        Identifica itens muito cotados que não puderam ser atendidos por falta de estoque.
        """
        sql = self._read_sql("queries_popularity_summary.sql")
        params = {
            "INI": ini,
            "FIN": fin,
            "EMPRESA": empresa,
            "CODPROD": codprod,
            "CODGRUPOPROD": grupoprod,
            "CODTIPVENDA": None,
            "VENDEDOR": None,
            "CODTIPPARC": None,
            "MOTIVOCANCEL": None
        }
        return self._execute_with_params(sql, params)

    # Skill 1: Popularidade e Demanda Reprimida (Drilldown)
    def get_popularity_drilldown(self, codprod: int, ini: str, fin: str, empresa: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Skill: Drilldown de Orçamentos por Produto.
        Lista todos os orçamentos de um item específico com o status de estoque na data.
        """
        sql = self._read_sql("queries_popularity_drilldown.sql")
        params = {
            "CODPROD": codprod,
            "INI": ini,
            "FIN": fin,
            "EMPRESA": empresa,
            "CODTIPVENDA": None,
            "VENDEDOR": None,
            "CODTIPPARC": None,
            "MOTIVOCANCEL": None
        }
        return self._execute_with_params(sql, params)

    # Skill 2: Inteligência de Fornecedores
    def get_suppliers_for_product(self, ini: str, fin: str, empresa: str, codprod: Optional[int] = None, grupoprod: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Mapeia quais fornecedores já venderam determinado item ou grupo.
        """
        sql = self._read_sql("queries_suppliers_list.sql")
        params = {
            "INI": ini,
            "FIN": fin,
            "EMPRESA": empresa,
            "CODPROD": codprod,
            "GRUPOPROD": grupoprod,
            "CODPARC": None
        }
        return self._execute_with_params(sql, params)

    def get_supplier_purchase_summary(self, codparc: int, ini: str, fin: str, empresa: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retorna grupos e produtos comprados de um fornecedor específico.
        """
        sql_groups = self._read_sql("queries_supplier_groups.sql")
        sql_products = self._read_sql("queries_supplier_products.sql")
        
        params = {
            "CODPARC": codparc,
            "INI": ini,
            "FIN": fin,
            "EMPRESA": empresa
        }
        
        return {
            "grupos": self._execute_with_params(sql_groups, params),
            "produtos": self._execute_with_params(sql_products, params)
        }

    # Skill 3: Equilíbrio Financeiro e Saúde do Capital de Giro
    def get_financial_procurement_balance(self, dias_horizonte: int = 30) -> Dict[str, Any]:
        """
        Skill: Inteligência de Capital de Giro.
        Analisa a transformação de Caixa em Estoque e o equilíbrio Pagar vs Receber.
        """
        sql_cash = self._read_sql("queries_financial_cash_flow.sql")
        sql_flow_comp = self._read_sql("queries_financial_flow_comparison.sql")
        sql_inventory = self._read_sql("queries_inventory_valuation.sql")
        sql_sales_avg = self._read_sql("queries_sales_average.sql")

        params = {"DIAS_HORIZONTE": dias_horizonte}

        cash_flows = sankhya.execute_query(sql_cash)
        flow_comparison = self._execute_with_params(sql_flow_comp, params)
        inventory_valuation = sankhya.execute_query(sql_inventory)
        sales_averages = sankhya.execute_query(sql_sales_avg)

        # Processamento de Fluxo Pagar vs Receber
        total_receber_prazo = sum(item.get("TOTAL", 0) for item in flow_comparison if "RECEBER" in item.get("TIPO", "") and item.get("STATUS_VENCIMENTO") == "NO_PRAZO")
        total_apagar_prazo = sum(item.get("TOTAL", 0) for item in flow_comparison if "PAGAR" in item.get("TIPO", "") and item.get("STATUS_VENCIMENTO") == "NO_PRAZO")
        
        # Totais consolidados
        total_caixa = sum(item.get("SALDOREAL", 0) for item in cash_flows)
        total_estoque = sum(item.get("VALOR_TOTAL_ESTOQUE", 0) for item in inventory_valuation)
        media_venda_total = sum(item.get("MEDIA_VENDA_MENSAL", 0) for item in sales_averages)

        # Indicadores de Pressão sobre o Caixa
        pressao_compras = (total_apagar_prazo / total_receber_prazo) if total_receber_prazo > 0 else 0
        cobertura_estoque_meses = (total_estoque / media_venda_total) if media_venda_total > 0 else 0

        return {
            "saude_financeira": {
                "total_disponivel_caixa": total_caixa,
                "indice_apagar_vs_receber": round(pressao_compras, 2), # > 1 significa que estamos pagando mais que recebendo
                "aviso_pressao": "ALTA" if pressao_compras > 1.2 else "NORMAL"
            },
            "saude_estoque": {
                "valor_total_estoque": total_estoque,
                "cobertura_estoque_meses": round(cobertura_estoque_meses, 2), # Quantos meses o estoque atual dura sem novas compras
                "venda_media_mensal_referencia": round(media_venda_total, 2)
            },
            "balanco_patrimonial_operacional": {
                "proporcao_estoque_no_ativo": round((total_estoque / (total_caixa + total_estoque)) * 100, 1) if (total_caixa + total_estoque) > 0 else 0,
                "insight": "Cuidado: muito caixa transformado em estoque" if cobertura_estoque_meses > 3 else "Giro saudável"
            }
        }

    # Skill 4: Análise de Giro Direto
    def get_giro_data(self, codrel: int = 2535) -> List[Dict[str, Any]]:
        """
        Skill: Inteligência de Giro Direta.
        Recupera as sugestões já calculadas pelo Sankhya na tabela TGFGIR,
        focando nas empresas 1 e 5.
        """
        sql_giro = self._read_sql("queries_giro_direct.sql")
        params = {"CODREL": codrel}

        try:
            return self._execute_with_params(sql_giro, params)
        except Exception as e:
            logger.error(f"Erro ao buscar dados de Giro Direto para CODREL {codrel}: {e}")
            return []

    # Skill 4: Oportunidades por Fornecedor
    def get_opportunities(self, codrel: int = 2535) -> List[Dict[str, Any]]:
        """
        Skill: Inteligência de Pacotes de Compra.
        Agrupa sugestões por Fornecedor (CODPARCFORN).
        """
        sql_ops = self._read_sql("queries_opportunities_by_supplier.sql")
        params = {"CODREL": codrel}

        try:
            return self._execute_with_params(sql_ops, params)
        except Exception as e:
            logger.error(f"Erro ao buscar oportunidades de compra para CODREL {codrel}: {e}")
            return []
            
    # Skill 5: Giro Detalhado por Fornecedor (Agregado + Marca + Explicação)
    def get_supplier_items(self, codparc: int, codrel: int = 2535) -> List[Dict[str, Any]]:
        """
        Busca itens de um fornecedor, AGREGANDO estoque e sugestão de todas as empresas (1 e 5).
        Evita mostrar 'Estoque Zero' se houver saldo em outra filial.
        """
        sql = """
            SELECT 
                G.CODPROD,
                MAX(P.DESCRPROD) AS DESCRPROD,
                MAX(P.CODGRUPOPROD) AS CODGRUPOPROD,
                MAX(P.MARCA) AS MARCA,
                SUM(G.SUGCOMPRA) AS SUGCOMPRA,
                MAX(G.CUSTOGER) AS CUSTOGER,
                SUM(G.GIRODIARIO) AS GIRODIARIO,
                SUM(G.ESTOQUE) AS ESTOQUE,
                SUM(G.ESTMIN) AS ESTMIN,
                MAX(G.LEADTIME) AS LEADTIME,
                MAX(G.ULTVENDA) AS ULTVENDA
            FROM TGFGIR G
            JOIN TGFPRO P ON G.CODPROD = P.CODPROD
            -- Join para garantir que este é o fornecedor PRINCIPAL (Volume) do produto
            JOIN (
                SELECT CODPROD, CODPARC
                FROM (
                    SELECT 
                        ITE.CODPROD, 
                        CAB.CODPARC,
                        ROW_NUMBER() OVER (PARTITION BY ITE.CODPROD ORDER BY SUM(ITE.QTDNEG) DESC) as RN
                    FROM TGFITE ITE
                    JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
                    WHERE CAB.TIPMOV = 'O' AND CAB.STATUSNOTA = 'L'
                    GROUP BY ITE.CODPROD, CAB.CODPARC
                ) WHERE RN = 1
            ) F ON G.CODPROD = F.CODPROD
            WHERE G.CODREL = :CODREL
              AND F.CODPARC = :CODPARC
              AND G.CODEMP IN (1, 5)
            GROUP BY G.CODPROD
            HAVING SUM(G.SUGCOMPRA) > 0 -- Mostra apenas se houver sugestão global > 0
            ORDER BY MAX(P.MARCA), MAX(P.DESCRPROD) ASC
        """
        params = {"CODREL": codrel, "CODPARC": codparc}
        return self._execute_with_params(sql, params)

    # Skill 7: Análise Completa de Categoria (Marca ou Macro Grupo)
    def get_full_category_analysis(self, target_type: str, target_value: str, codrel: int = 2535) -> List[Dict[str, Any]]:
        """
        Busca TODOS os itens de uma categoria (Marca ou Macro Grupo), independente de sugestão de compra.
        Calcula agregado de estoque e venda para análise Buy/Hold/Sell.
        target_type: 'MARCA' ou 'MACRO_GRUPO'
        """
        filter_clause = ""
        if target_type == 'MARCA':
            filter_clause = "AND P.MARCA = :TARGET"
        elif target_type == 'MACRO_GRUPO':
            filter_clause = "AND GRU.AD_CATMACRO = :TARGET"
            
        sql = f"""
            SELECT 
                G.CODPROD,
                MAX(P.DESCRPROD) AS DESCRPROD,
                MAX(P.MARCA) AS MARCA,
                MAX(GRU.AD_CATMACRO) AS MACRO_GRUPO,
                SUM(G.SUGCOMPRA) AS SUGCOMPRA,
                MAX(G.CUSTOGER) AS CUSTOGER,
                SUM(G.GIRODIARIO) AS GIRODIARIO,
                SUM(G.ESTOQUE) AS ESTOQUE,
                MAX(G.LEADTIME) AS LEADTIME
            FROM TGFGIR G
            JOIN TGFPRO P ON G.CODPROD = P.CODPROD
            JOIN TGFGRU GRU ON P.CODGRUPOPROD = GRU.CODGRUPOPROD
            WHERE G.CODREL = :CODREL 
              AND G.CODEMP IN (1, 5)
              {filter_clause}
            GROUP BY G.CODPROD
            ORDER BY MAX(P.DESCRPROD) ASC
        """
        params = {"CODREL": codrel, "TARGET": target_value}
        return self._execute_with_params(sql, params)

    # Skill 6: Contexto de Família (Agrupamento)
    def get_group_stock_summary(self, codrel: int = 2535) -> Dict[int, float]:
        """
        Retorna o estoque total consolidado por Grupo de Produtos (CODGRUPOPROD).
        Usado para identificar se há 'vazamento' de estoque em produtos similares.
        """
        sql = """
            SELECT 
                P.CODGRUPOPROD, 
                SUM(G.ESTOQUE) as TOTAL_ESTOQUE
            FROM TGFGIR G
            JOIN TGFPRO P ON G.CODPROD = P.CODPROD
            WHERE G.CODREL = :CODREL
              AND G.CODEMP IN (1, 5)
            GROUP BY P.CODGRUPOPROD
        """
        params = {"CODREL": codrel}
        results = self._execute_with_params(sql, params)
        return {row['CODGRUPOPROD']: float(row['TOTAL_ESTOQUE']) for row in results}

    def get_alternatives(self, codprod: int) -> List[int]:
        """
        Busca produtos alternativos baseado na estratégia configurada.
        """
        strategy = self.config.get("alternatives", {}).get("strategy", "brand_group")
        
        if strategy == "brand_group":
            sql = f"""
            SELECT CODPROD 
            FROM TGFPRO 
            WHERE CODGRUPOPROD = (SELECT CODGRUPOPROD FROM TGFPRO WHERE CODPROD = {codprod})
              AND MARCA = (SELECT MARCA FROM TGFPRO WHERE CODPROD = {codprod})
              AND CODPROD <> {codprod}
              AND ATIVO = 'S'
            """
        else:
            sql = self._read_sql(self.config.get("alternatives", {}).get("custom_sql_path", "queries_alternatives.sql"))
            sql = sql.replace(":CODPROD", str(codprod))

        try:
            rows = sankhya.execute_query(sql)
            return [int(row["CODPROD"]) for row in rows]
        except Exception as e:
            logger.error(f"Erro ao buscar alternativos para {codprod}: {e}")
            return []
