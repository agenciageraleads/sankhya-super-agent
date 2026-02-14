-- Query: Budget Allocation (Distribuição de Orçamento por Fornecedor)
-- Distribui orçamento de compras baseado em:
-- - CMV do mês anterior × 1.0167 (crescimento de 20% a.a.)
-- - Índice de margem por fornecedor (maior margem = maior budget)
-- - 5% reservado para "exploration pool" (novos fornecedores)

WITH CMVBase AS (
    -- CMV do mês anterior (reutiliza queries_cmv_previous_month.sql)
    WITH VendasMesAnterior AS (
        SELECT
            CAB.CODEMP,
            ITE.CODPROD,
            SUM(ITE.QTDNEG) AS QTD_VENDIDA
        FROM TGFCAB CAB
        JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        WHERE CAB.TIPMOV = 'V'
          AND CAB.STATUSNOTA = 'L'
          AND CAB.DTNEG >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM')
          AND CAB.DTNEG < TRUNC(SYSDATE, 'MM')
          AND CAB.CODEMP IN (1, 5)
        GROUP BY CAB.CODEMP, ITE.CODPROD
    ),
    CustoAtual AS (
        SELECT
            C.CODEMP,
            C.CODPROD,
            C.CUSREP
        FROM TGFCUS C
        WHERE C.DHALTER = (
            SELECT MAX(C2.DHALTER)
            FROM TGFCUS C2
            WHERE C2.CODPROD = C.CODPROD
              AND C2.CODEMP = C.CODEMP
        )
    )
    SELECT SUM(S.QTD_VENDIDA * COALESCE(LC.CUSREP, 0)) AS CMV_TOTAL
    FROM VendasMesAnterior S
    LEFT JOIN CustoAtual LC ON S.CODPROD = LC.CODPROD AND S.CODEMP = LC.CODEMP
),
GrowthProjection AS (
    -- Aplicar fator de crescimento: 20% a.a. = 1.67% mensal
    -- Fórmula: (1 + 0.20)^(1/12) ≈ 1.0167
    SELECT
        CMV_TOTAL,
        ROUND(CMV_TOTAL * 1.0167, 2) AS ORCAMENTO_MES_ATUAL,
        ROUND(CMV_TOTAL * 1.0167 * 0.05, 2) AS RESERVA_EXPLORACAO  -- 5% para novos fornecedores
    FROM CMVBase
),
SupplierScores AS (
    -- Índices de prioridade por fornecedor (reutiliza queries_supplier_margin_index.sql)
    WITH ComprasPorFornecedor AS (
        SELECT
            CAB.CODPARC,
            ITE.CODPROD,
            AVG(ITE.VLRUNIT) AS CUSTO_MEDIO_COMPRA,
            SUM(ITE.QTDNEG) AS VOLUME_COMPRADO,
            SUM(ITE.VLRTOT) AS VALOR_TOTAL_COMPRADO
        FROM TGFCAB CAB
        JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        WHERE CAB.TIPMOV = 'C'
          AND CAB.STATUSNOTA = 'L'
          AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)
          AND CAB.CODEMP IN (1, 5)
        GROUP BY CAB.CODPARC, ITE.CODPROD
        HAVING SUM(ITE.QTDNEG) > 0
    ),
    VendasProduto AS (
        SELECT
            ITE.CODPROD,
            AVG(ITE.VLRUNIT) AS PRECO_MEDIO_VENDA
        FROM TGFCAB CAB
        JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        WHERE CAB.TIPMOV = 'V'
          AND CAB.STATUSNOTA = 'L'
          AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)
          AND CAB.CODEMP IN (1, 5)
        GROUP BY ITE.CODPROD
    ),
    MargemCalculation AS (
        SELECT
            CP.CODPARC,
            CASE
                WHEN CP.CUSTO_MEDIO_COMPRA > 0 THEN
                    ((VP.PRECO_MEDIO_VENDA - CP.CUSTO_MEDIO_COMPRA) / CP.CUSTO_MEDIO_COMPRA) * 100
                ELSE 0
            END AS MARGEM_PERCENTUAL,
            CP.VOLUME_COMPRADO
        FROM ComprasPorFornecedor CP
        JOIN VendasProduto VP ON CP.CODPROD = VP.CODPROD
        WHERE VP.PRECO_MEDIO_VENDA > CP.CUSTO_MEDIO_COMPRA
    )
    SELECT
        CODPARC,
        ROUND(AVG(MARGEM_PERCENTUAL) * SQRT(SUM(VOLUME_COMPRADO)), 2) AS INDICE_PRIORIDADE
    FROM MargemCalculation
    GROUP BY CODPARC
    HAVING AVG(MARGEM_PERCENTUAL) >= 5
),
TotalScore AS (
    -- Soma dos índices para cálculo proporcional
    SELECT SUM(INDICE_PRIORIDADE) AS SOMA_INDICES
    FROM SupplierScores
)
-- Distribuição final: 95% distribuído proporcionalmente, 5% exploration
SELECT
    SS.CODPARC,
    PAR.NOMEPARC,
    GP.ORCAMENTO_MES_ATUAL AS ORCAMENTO_GLOBAL,
    GP.CMV_TOTAL AS CMV_BASE,
    SS.INDICE_PRIORIDADE,
    -- Alocação: (Budget - Exploration) × (Índice Fornecedor / Soma Índices)
    ROUND(
        ((GP.ORCAMENTO_MES_ATUAL - GP.RESERVA_EXPLORACAO) * SS.INDICE_PRIORIDADE / TS.SOMA_INDICES),
        2
    ) AS ORCAMENTO_ALOCADO,
    ROUND(
        (SS.INDICE_PRIORIDADE / TS.SOMA_INDICES) * 100,
        1
    ) AS PERCENTUAL_ALOCACAO
FROM SupplierScores SS
CROSS JOIN GrowthProjection GP
CROSS JOIN TotalScore TS
JOIN TGFPAR PAR ON SS.CODPARC = PAR.CODPARC
WHERE SS.INDICE_PRIORIDADE > 0
ORDER BY ORCAMENTO_ALOCADO DESC
