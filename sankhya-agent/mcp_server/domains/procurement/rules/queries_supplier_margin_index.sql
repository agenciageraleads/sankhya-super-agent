-- Query: Supplier Margin Index (Índice de Margem por Fornecedor)
-- Calcula prioridade de fornecedores baseado em margem de lucro
-- Fórmula: Índice = Margem Média × √(Volume Comprado)
-- Usado para distribuir orçamento de compras priorizando fornecedores lucrativos

WITH ComprasPorFornecedor AS (
    -- Custo médio de compra por fornecedor nos últimos 6 meses
    SELECT
        CAB.CODPARC,
        ITE.CODPROD,
        AVG(ITE.VLRUNIT) AS CUSTO_MEDIO_COMPRA,
        SUM(ITE.QTDNEG) AS VOLUME_COMPRADO,
        SUM(ITE.VLRTOT) AS VALOR_TOTAL_COMPRADO
    FROM TGFCAB CAB
    JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
    WHERE CAB.TIPMOV = 'C'  -- Compras
      AND CAB.STATUSNOTA = 'L'  -- Liberadas
      AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)  -- Últimos 6 meses
      AND CAB.CODEMP IN (1, 5)
    GROUP BY CAB.CODPARC, ITE.CODPROD
    HAVING SUM(ITE.QTDNEG) > 0  -- Apenas produtos com volume
),
VendasProduto AS (
    -- Preço médio de venda por produto nos últimos 6 meses
    SELECT
        ITE.CODPROD,
        AVG(ITE.VLRUNIT) AS PRECO_MEDIO_VENDA,
        SUM(ITE.QTDNEG) AS VOLUME_VENDIDO
    FROM TGFCAB CAB
    JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
    WHERE CAB.TIPMOV = 'V'  -- Vendas
      AND CAB.STATUSNOTA = 'L'
      AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)
      AND CAB.CODEMP IN (1, 5)
    GROUP BY ITE.CODPROD
    HAVING SUM(ITE.QTDNEG) > 0
),
MargemCalculation AS (
    -- Cálculo de margem produto a produto
    SELECT
        CP.CODPARC,
        PAR.NOMEPARC,
        CP.CODPROD,
        MAX(P.DESCRPROD) AS DESCRPROD,
        CP.CUSTO_MEDIO_COMPRA,
        VP.PRECO_MEDIO_VENDA,
        -- Margem percentual: ((Venda - Custo) / Custo) × 100
        CASE
            WHEN CP.CUSTO_MEDIO_COMPRA > 0 THEN
                ROUND(
                    ((VP.PRECO_MEDIO_VENDA - CP.CUSTO_MEDIO_COMPRA) / CP.CUSTO_MEDIO_COMPRA) * 100,
                    2
                )
            ELSE 0
        END AS MARGEM_PERCENTUAL,
        CP.VOLUME_COMPRADO,
        VP.VOLUME_VENDIDO,
        CP.VALOR_TOTAL_COMPRADO
    FROM ComprasPorFornecedor CP
    JOIN VendasProduto VP ON CP.CODPROD = VP.CODPROD
    JOIN TGFPAR PAR ON CP.CODPARC = PAR.CODPARC
    JOIN TGFPRO P ON CP.CODPROD = P.CODPROD
    WHERE VP.PRECO_MEDIO_VENDA > CP.CUSTO_MEDIO_COMPRA  -- Apenas produtos lucrativos
      AND (:CODPARC IS NULL OR CP.CODPARC = :CODPARC)
)
-- Agregação por fornecedor com índice de prioridade
SELECT
    CODPARC,
    MAX(NOMEPARC) AS NOMEPARC,
    COUNT(DISTINCT CODPROD) AS MIX_PRODUTOS,
    ROUND(AVG(MARGEM_PERCENTUAL), 2) AS MARGEM_MEDIA,
    ROUND(MIN(MARGEM_PERCENTUAL), 2) AS MARGEM_MIN,
    ROUND(MAX(MARGEM_PERCENTUAL), 2) AS MARGEM_MAX,
    SUM(VOLUME_COMPRADO) AS VOLUME_TOTAL_COMPRADO,
    ROUND(SUM(VALOR_TOTAL_COMPRADO), 2) AS VALOR_TOTAL_COMPRADO,
    -- Índice de prioridade: Margem × √Volume (amortiza outliers)
    ROUND(
        AVG(MARGEM_PERCENTUAL) * SQRT(SUM(VOLUME_COMPRADO)),
        2
    ) AS INDICE_PRIORIDADE
FROM MargemCalculation
GROUP BY CODPARC
HAVING AVG(MARGEM_PERCENTUAL) >= 5  -- Margem mínima de 5%
ORDER BY INDICE_PRIORIDADE DESC
