-- Query: Effective Lead Time with Fallback Strategy
-- Prioridade: Histórico 6mo → Categoria do fornecedor → Estático TGFGIR → Default 30d
-- Retorna lead time mais confiável disponível com indicador de fonte

WITH HistoricalLeadTime AS (
    -- Priority 1: Lead time histórico do produto-fornecedor
    SELECT
        CODPARC,
        CODPROD,
        LEADTIME_PONDERADO,
        NUM_ENTREGAS,
        'HISTORICO' AS FONTE
    FROM (
        -- Reutiliza lógica de queries_leadtime_history.sql
        WITH PurchaseOrderDates AS (
            SELECT
                CAB.NUNOTA AS NUNOTA_COMPRA,
                CAB.CODPARC,
                CAB.DTNEG AS DATA_PEDIDO,
                ITE.CODPROD,
                ITE.QTDNEG AS QTD_PEDIDA
            FROM TGFCAB CAB
            JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.TIPMOV = 'O'
              AND CAB.STATUSNOTA = 'L'
              AND CAB.CODTIPOPER IN (200, 227)
              AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)  -- Apenas últimos 6 meses
              AND CAB.CODPARC = :CODPARC
              AND ITE.CODPROD = :CODPROD
        ),
        InvoiceReceipts AS (
            SELECT
                VAR.NUNOTAORIG AS NUNOTA_COMPRA,
                VAR.CODPROD,
                CAB_INV.DTENTSAI AS DATA_RECEBIMENTO,
                VAR.QTDNEG AS QTD_RECEBIDA
            FROM TGFVAR VAR
            JOIN TGFCAB CAB_INV ON VAR.NUNOTA = CAB_INV.NUNOTA
            WHERE CAB_INV.TIPMOV = 'C'
              AND CAB_INV.STATUSNOTA = 'L'
              AND CAB_INV.DTENTSAI IS NOT NULL
              AND VAR.NUNOTAORIG IS NOT NULL
              AND CAB_INV.DTENTSAI >= ADD_MONTHS(SYSDATE, -6)
        ),
        LeadTimeCalculations AS (
            SELECT
                PO.CODPARC,
                PO.CODPROD,
                (IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO) AS LEADTIME_DIAS,
                CASE
                    WHEN IR.DATA_RECEBIMENTO >= ADD_MONTHS(SYSDATE, -3) THEN 0.7
                    ELSE 0.3
                END AS PESO_TEMPORAL
            FROM PurchaseOrderDates PO
            JOIN InvoiceReceipts IR
                ON PO.NUNOTA_COMPRA = IR.NUNOTA_COMPRA
                AND PO.CODPROD = IR.CODPROD
            WHERE (IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO) BETWEEN 0 AND 180
        )
        SELECT
            CODPARC,
            CODPROD,
            COUNT(*) AS NUM_ENTREGAS,
            ROUND(SUM(LEADTIME_DIAS * PESO_TEMPORAL) / SUM(PESO_TEMPORAL), 1) AS LEADTIME_PONDERADO
        FROM LeadTimeCalculations
        GROUP BY CODPARC, CODPROD
        HAVING COUNT(*) >= 2
    )
    WHERE CODPARC = :CODPARC AND CODPROD = :CODPROD
),
SupplierCategoryAvg AS (
    -- Priority 2: Média da categoria de produtos do fornecedor
    SELECT
        H.CODPARC,
        P.CODGRUPOPROD,
        ROUND(AVG(H.LEADTIME_PONDERADO), 1) AS LEADTIME_CATEGORIA,
        'CATEGORIA' AS FONTE
    FROM (
        -- Histórico consolidado por categoria
        WITH PO AS (
            SELECT
                CAB.NUNOTA AS NUNOTA_COMPRA,
                CAB.CODPARC,
                CAB.DTNEG AS DATA_PEDIDO,
                ITE.CODPROD
            FROM TGFCAB CAB
            JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.TIPMOV = 'O'
              AND CAB.STATUSNOTA = 'L'
              AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -6)
              AND CAB.CODPARC = :CODPARC
        ),
        IR AS (
            SELECT
                VAR.NUNOTAORIG AS NUNOTA_COMPRA,
                VAR.CODPROD,
                CAB_INV.DTENTSAI AS DATA_RECEBIMENTO
            FROM TGFVAR VAR
            JOIN TGFCAB CAB_INV ON VAR.NUNOTA = CAB_INV.NUNOTA
            WHERE CAB_INV.TIPMOV = 'C'
              AND CAB_INV.STATUSNOTA = 'L'
              AND CAB_INV.DTENTSAI IS NOT NULL
              AND VAR.NUNOTAORIG IS NOT NULL
        )
        SELECT
            PO.CODPARC,
            PO.CODPROD,
            ROUND(AVG(IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO), 1) AS LEADTIME_PONDERADO
        FROM PO
        JOIN IR ON PO.NUNOTA_COMPRA = IR.NUNOTA_COMPRA AND PO.CODPROD = IR.CODPROD
        WHERE (IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO) BETWEEN 0 AND 180
        GROUP BY PO.CODPARC, PO.CODPROD
        HAVING COUNT(*) >= 2
    ) H
    JOIN TGFPRO P ON H.CODPROD = P.CODPROD
    WHERE H.CODPARC = :CODPARC
    GROUP BY H.CODPARC, P.CODGRUPOPROD
    HAVING COUNT(DISTINCT H.CODPROD) >= 3  -- Categoria com pelo menos 3 produtos
),
StaticGIR AS (
    -- Priority 3: Valor estático do TGFGIR
    SELECT
        G.CODPROD,
        MAX(G.LEADTIME) AS LEADTIME_ESTATICO,
        'ESTATICO' AS FONTE
    FROM TGFGIR G
    WHERE G.CODPROD = :CODPROD
      AND G.CODEMP IN (1, 5)
    GROUP BY G.CODPROD
)
-- Final: retorna lead time efetivo com fallback em cascata
SELECT
    :CODPROD AS CODPROD,
    :CODPARC AS CODPARC,
    COALESCE(
        -- Priority 1: Histórico produto-fornecedor (últimos 6 meses)
        (SELECT LEADTIME_PONDERADO
         FROM HistoricalLeadTime
         WHERE CODPROD = :CODPROD AND CODPARC = :CODPARC),

        -- Priority 2: Média da categoria do fornecedor
        (SELECT SCA.LEADTIME_CATEGORIA
         FROM SupplierCategoryAvg SCA
         JOIN TGFPRO P ON P.CODPROD = :CODPROD
         WHERE SCA.CODPARC = :CODPARC
           AND SCA.CODGRUPOPROD = P.CODGRUPOPROD),

        -- Priority 3: Valor estático TGFGIR
        (SELECT LEADTIME_ESTATICO
         FROM StaticGIR
         WHERE CODPROD = :CODPROD),

        -- Priority 4: Default conservador (30 dias)
        30
    ) AS LEADTIME_EFETIVO,

    -- Indicador de fonte (para auditoria/confiabilidade)
    CASE
        WHEN EXISTS (SELECT 1 FROM HistoricalLeadTime
                     WHERE CODPROD = :CODPROD AND CODPARC = :CODPARC)
        THEN 'HISTORICO'

        WHEN EXISTS (SELECT 1 FROM SupplierCategoryAvg SCA
                     JOIN TGFPRO P ON P.CODPROD = :CODPROD
                     WHERE SCA.CODPARC = :CODPARC
                       AND SCA.CODGRUPOPROD = P.CODGRUPOPROD)
        THEN 'CATEGORIA'

        WHEN EXISTS (SELECT 1 FROM StaticGIR WHERE CODPROD = :CODPROD)
        THEN 'ESTATICO'

        ELSE 'DEFAULT'
    END AS FONTE_LEADTIME

FROM DUAL
