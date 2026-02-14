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
        elif target_type == 'GRUPO':
            filter_clause = "AND GRU.DESCRGRUPOPROD LIKE '%' || :TARGET || '%'"
            
        sql = f"""
            SELECT 
                G.CODPROD,
                MAX(P.DESCRPROD) AS DESCRPROD,
                MAX(P.MARCA) AS MARCA,
                MAX(GRU.AD_CATMACRO) AS MACRO_GRUPO,
                MAX(GRU.DESCRGRUPOPROD) AS GRUPO,
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

    # === NOVOS MÉTODOS: Lead Time Dinâmico ===

    def get_supplier_leadtime_history(self, codparc: int, codprod: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Histórico de lead time do fornecedor.
        Retorna estatísticas de entregas reais (pedido → nota fiscal).
        """
        sql = self._read_sql("queries_leadtime_history.sql")
        params = {"CODPARC": codparc, "CODPROD": codprod}
        return self._execute_with_params(sql, params)

    def get_effective_leadtime(self, codprod: int, codparc: int) -> Dict[str, Any]:
        """
        Lead time efetivo com estratégia de fallback.
        Priority: Histórico → Categoria → Estático → Default (30d)
        """
        sql = self._read_sql("queries_leadtime_effective.sql")
        params = {"CODPROD": codprod, "CODPARC": codparc}
        results = self._execute_with_params(sql, params)

        if results:
            return {
                "leadtime_dias": float(results[0]["LEADTIME_EFETIVO"]),
                "fonte": results[0]["FONTE_LEADTIME"],
                "confiavel": results[0]["FONTE_LEADTIME"] in ["HISTORICO", "CATEGORIA"]
            }
        return {"leadtime_dias": 30, "fonte": "DEFAULT", "confiavel": False}

    # === NOVOS MÉTODOS: CMV Budget Control ===

    def get_cmv_previous_month(self, codemp: Optional[int] = None) -> Dict[str, Any]:
        """
        Calcula CMV (Custo de Mercadoria Vendida) do mês anterior.
        Base para orçamento de compras do mês atual.
        """
        sql = self._read_sql("queries_cmv_previous_month.sql")
        try:
            results = sankhya.execute_query(sql)
            if codemp:
                results = [r for r in results if r.get("CODEMP") == codemp]

            total_cmv = sum(float(r.get("CMV_TOTAL", 0)) for r in results)

            return {
                "cmv_mes_anterior": total_cmv,
                "detalhamento_empresas": results,
                "itens_vendidos": sum(int(r.get("ITENS_VENDIDOS", 0)) for r in results)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular CMV: {e}")
            return {"cmv_mes_anterior": 0, "detalhamento_empresas": [], "itens_vendidos": 0}

    def get_supplier_margin_index(self, codparc: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calcula índice de margem por fornecedor.
        Maior índice = maior prioridade para alocação de budget.
        """
        sql = self._read_sql("queries_supplier_margin_index.sql")
        params = {"CODPARC": codparc}
        return self._execute_with_params(sql, params)

    def calculate_purchase_budget_allocation(self, growth_factor: float = 0.20) -> Dict[str, Any]:
        """
        Calcula orçamento global e distribui entre fornecedores.

        Args:
            growth_factor: Crescimento anual esperado (default: 20% = 0.20)

        Returns:
            {
                "orcamento_global": float,
                "cmv_base": float,
                "fator_crescimento_mensal": str,
                "alocacao_fornecedores": List[Dict],
                "reserva_exploracao": float
            }
        """
        # Calcular CMV base
        cmv_data = self.get_cmv_previous_month()
        cmv_base = cmv_data["cmv_mes_anterior"]

        # Crescimento mensal composto: (1 + 0.20)^(1/12) - 1 ≈ 0.0167
        monthly_rate = ((1 + growth_factor) ** (1/12)) - 1
        budget_total = cmv_base * (1 + monthly_rate)

        # Buscar alocações por fornecedor
        sql_allocation = self._read_sql("queries_budget_allocation.sql")
        try:
            allocations = sankhya.execute_query(sql_allocation)
        except Exception as e:
            logger.error(f"Erro ao calcular alocação de budget: {e}")
            allocations = []

        return {
            "orcamento_global": round(budget_total, 2),
            "cmv_base": round(cmv_base, 2),
            "fator_crescimento_anual": f"{growth_factor * 100}%",
            "fator_crescimento_mensal": f"{monthly_rate * 100:.2f}%",
            "fonte_calculo": "CMV mês anterior × 1.0167",
            "alocacao_fornecedores": allocations,
            "reserva_exploracao": round(budget_total * 0.05, 2)
        }

    def validate_purchase_against_budget(self, codparc: int, valor_compra: float) -> Dict[str, Any]:
        """
        HARD CAP: Valida se compra pode ser realizada dentro do orçamento alocado.

        Returns:
            {
                "aprovado": bool,
                "orcamento_disponivel": float,
                "valor_solicitado": float,
                "mensagem": str
            }
        """
        # 1. Buscar orçamento alocado do fornecedor
        budget_data = self.calculate_purchase_budget_allocation()
        supplier_allocations = {
            int(a["CODPARC"]): float(a["ORCAMENTO_ALOCADO"])
            for a in budget_data["alocacao_fornecedores"]
        }

        # 2. Buscar gastos acumulados no mês atual
        sql_spent = """
            SELECT SUM(ITE.VLRTOT) AS GASTO_ACUMULADO
            FROM TGFCAB CAB
            JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.CODPARC = :CODPARC
              AND CAB.TIPMOV = 'O'
              AND CAB.STATUSNOTA = 'L'
              AND CAB.DTNEG >= TRUNC(SYSDATE, 'MM')
        """
        spent_results = self._execute_with_params(sql_spent, {"CODPARC": codparc})
        gasto_acumulado = float(spent_results[0].get("GASTO_ACUMULADO", 0)) if spent_results else 0

        # 3. Calcular disponível
        orcamento_fornecedor = supplier_allocations.get(codparc, budget_data["reserva_exploracao"])
        disponivel = orcamento_fornecedor - gasto_acumulado
        aprovado = (valor_compra <= disponivel)
        percentual_utilizado = ((gasto_acumulado + valor_compra) / orcamento_fornecedor * 100) if orcamento_fornecedor > 0 else 0

        return {
            "aprovado": aprovado,
            "orcamento_alocado": round(orcamento_fornecedor, 2),
            "gasto_acumulado": round(gasto_acumulado, 2),
            "orcamento_disponivel": round(disponivel, 2),
            "valor_solicitado": round(valor_compra, 2),
            "percentual_utilizado": round(percentual_utilizado, 1),
            "mensagem": (
                f"✅ APROVADO: R$ {valor_compra:,.2f} dentro do limite (disponível: R$ {disponivel:,.2f})"
                if aprovado else
                f"❌ BLOQUEADO: R$ {valor_compra:,.2f} excede orçamento de R$ {disponivel:,.2f}"
            )
        }
