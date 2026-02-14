-- Query: Historical Lead Time Analysis
-- Calcula lead time real baseado em pedidos de compra → notas de entrada
-- Relacionamento: TGFVAR.NUNOTAORIG (nota) → TGFCAB.NUNOTA (pedido)
-- Fórmula: TGFCAB.DTENTSAI - TGFCAB.DTNEG (ambos em TGFCAB)
-- Peso temporal: últimos 3m = 70%, 3-6m = 30%, 6-12m = 10%

WITH PurchaseOrderDates AS (
    -- Pedidos de compra com data de negociação
    SELECT
        CAB.NUNOTA AS NUNOTA_COMPRA,
        CAB.CODPARC,
        CAB.DTNEG AS DATA_PEDIDO,
        ITE.CODPROD,
        ITE.QTDNEG AS QTD_PEDIDA
    FROM TGFCAB CAB
    JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
    WHERE CAB.TIPMOV = 'O'  -- Ordem de Compra
      AND CAB.STATUSNOTA = 'L'  -- Liberada
      AND CAB.CODTIPOPER IN (200, 227)  -- Tipos operacionais de compra
      AND CAB.DTNEG >= ADD_MONTHS(SYSDATE, -12)  -- Últimos 12 meses
      AND (:CODPARC IS NULL OR CAB.CODPARC = :CODPARC)
      AND (:CODPROD IS NULL OR ITE.CODPROD = :CODPROD)
),
InvoiceReceipts AS (
    -- Notas fiscais de entrada com data de recebimento
    SELECT
        VAR.NUNOTAORIG AS NUNOTA_COMPRA,
        VAR.CODPROD,
        CAB_INV.DTENTSAI AS DATA_RECEBIMENTO,
        CAB_INV.NUNOTA AS NUNOTA_ENTRADA,
        VAR.QTDNEG AS QTD_RECEBIDA
    FROM TGFVAR VAR
    JOIN TGFCAB CAB_INV ON VAR.NUNOTA = CAB_INV.NUNOTA
    WHERE CAB_INV.TIPMOV = 'C'  -- Compra (entrada)
      AND CAB_INV.STATUSNOTA = 'L'  -- Liberada
      AND CAB_INV.DTENTSAI IS NOT NULL  -- Deve ter data de entrada
      AND VAR.NUNOTAORIG IS NOT NULL  -- Deve ter referência ao pedido
      AND CAB_INV.DTENTSAI >= ADD_MONTHS(SYSDATE, -12)
),
LeadTimeCalculations AS (
    -- Calcula lead time individual para cada entrega
    SELECT
        PO.CODPARC,
        PO.CODPROD,
        PO.NUNOTA_COMPRA,
        IR.NUNOTA_ENTRADA,
        PO.DATA_PEDIDO,
        IR.DATA_RECEBIMENTO,
        (IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO) AS LEADTIME_DIAS,
        IR.QTD_RECEBIDA,
        PO.QTD_PEDIDA,
        -- Peso temporal: mais recente = maior peso
        CASE
            WHEN IR.DATA_RECEBIMENTO >= ADD_MONTHS(SYSDATE, -3) THEN 0.7  -- Últimos 3 meses
            WHEN IR.DATA_RECEBIMENTO >= ADD_MONTHS(SYSDATE, -6) THEN 0.3  -- 3-6 meses
            ELSE 0.1  -- 6-12 meses
        END AS PESO_TEMPORAL
    FROM PurchaseOrderDates PO
    JOIN InvoiceReceipts IR
        ON PO.NUNOTA_COMPRA = IR.NUNOTA_COMPRA
        AND PO.CODPROD = IR.CODPROD
    WHERE (IR.DATA_RECEBIMENTO - PO.DATA_PEDIDO) BETWEEN 0 AND 180  -- Filtro de outliers
)
-- Agregação final por fornecedor + produto
SELECT
    CODPARC,
    CODPROD,
    COUNT(*) AS NUM_ENTREGAS,
    ROUND(AVG(LEADTIME_DIAS), 1) AS LEADTIME_MEDIO_SIMPLES,
    ROUND(
        SUM(LEADTIME_DIAS * PESO_TEMPORAL) / SUM(PESO_TEMPORAL),
        1
    ) AS LEADTIME_PONDERADO,
    MIN(LEADTIME_DIAS) AS LEADTIME_MIN,
    MAX(LEADTIME_DIAS) AS LEADTIME_MAX,
    ROUND(STDDEV(LEADTIME_DIAS), 1) AS LEADTIME_DESVIO,
    MIN(DATA_RECEBIMENTO) AS PRIMEIRA_ENTREGA,
    MAX(DATA_RECEBIMENTO) AS ULTIMA_ENTREGA
FROM LeadTimeCalculations
GROUP BY CODPARC, CODPROD
HAVING COUNT(*) >= 2  -- Mínimo 2 entregas para validade estatística
ORDER BY ULTIMA_ENTREGA DESC
