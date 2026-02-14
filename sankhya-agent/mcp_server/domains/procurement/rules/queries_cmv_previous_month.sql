-- Query: CMV (Custo de Mercadoria Vendida) do Mês Anterior
-- Calcula o custo real dos produtos vendidos no mês anterior
-- Fórmula: CMV = SUM(Quantidade Vendida × Custo de Reposição)
-- Usado como base para orçamento de compras do mês atual

WITH VendasMesAnterior AS (
    -- Vendas liberadas do mês anterior
    SELECT
        CAB.CODEMP,
        ITE.CODPROD,
        SUM(ITE.QTDNEG) AS QTD_VENDIDA,
        MAX(P.DESCRPROD) AS DESCRPROD,
        MAX(P.CODGRUPOPROD) AS CODGRUPOPROD
    FROM TGFCAB CAB
    JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
    JOIN TGFPRO P ON ITE.CODPROD = P.CODPROD
    WHERE CAB.TIPMOV = 'V'  -- Vendas
      AND CAB.STATUSNOTA = 'L'  -- Liberadas
      -- Data: início do mês anterior até fim do mês anterior
      AND CAB.DTNEG >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM')
      AND CAB.DTNEG < TRUNC(SYSDATE, 'MM')
      AND CAB.CODEMP IN (1, 5)
    GROUP BY CAB.CODEMP, ITE.CODPROD
),
CustoAtual AS (
    -- Custo de reposição mais recente por produto
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
-- Agregação: CMV por empresa
SELECT
    S.CODEMP,
    SUM(S.QTD_VENDIDA * COALESCE(LC.CUSREP, 0)) AS CMV_TOTAL,
    COUNT(DISTINCT S.CODPROD) AS ITENS_VENDIDOS,
    ROUND(AVG(S.QTD_VENDIDA * COALESCE(LC.CUSREP, 0)), 2) AS CMV_MEDIO_POR_ITEM,
    MIN(S.CODGRUPOPROD) AS EXEMPLO_GRUPO  -- Para debug
FROM VendasMesAnterior S
LEFT JOIN CustoAtual LC
    ON S.CODPROD = LC.CODPROD
    AND S.CODEMP = LC.CODEMP
GROUP BY S.CODEMP
ORDER BY S.CODEMP
