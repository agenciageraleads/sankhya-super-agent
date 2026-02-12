-- Saldo Real em Caixa e Bancos
-- Retorna o saldo consolidado de todas as contas ativas
SELECT 
    CODCTABCOINT,
    DESCRICAO AS CONTA,
    SALDOREAL,
    CODEMP
FROM TSICTA 
WHERE ATIVA = 'S'
  AND SALDOREAL <> 0
ORDER BY CODEMP, SALDOREAL DESC
