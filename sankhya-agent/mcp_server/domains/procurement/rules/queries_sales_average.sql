-- Média de Vendas Mensais (Últimos 3 meses)
-- Usado para calcular a cobertura de estoque
SELECT 
    CODEMP,
    SUM(VLRNOTA) / 3 AS MEDIA_VENDA_MENSAL
FROM TGFCAB 
WHERE TIPMOV = 'V'
  AND (STATUSNOTA = 'L' OR CODTIPOPER = 1150)
  AND DTNEG > ADD_MONTHS(SYSDATE, -3)
GROUP BY CODEMP
