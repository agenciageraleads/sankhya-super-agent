-- Busca Inteligente da Matriz de Giro (TGFGIR)
-- Recupera as sugestões já calculadas pelo Sankhya, enriquecendo com dados do produto.
-- Filtrando empresas 1 e 5 conforme diretriz estratégica.
SELECT 
    G.CODPROD,
    P.DESCRPROD,
    P.CODGRUPOPROD,
    G.CODEMP,
    G.SUGCOMPRA,
    G.SUGCOMPRAGIR,
    G.ESTMIN,
    G.ESTMAX,
    G.GIRODIARIO,      -- Corrigido de GIRODIA
    G.ESTOQUE,         -- Corrigido de SALDO
    G.LEADTIME,
    G.ULTVENDA,        -- Corrigido de DTULTVENDA (se for Data) ou verificando campo
    G.CODVOL,
    G.CODVOLCOMPRA,
    G.DUREST,          -- Duração de Estoque calculada
    G.DIASSEMVENDA     -- Dias sem venda
FROM TGFGIR G
JOIN TGFPRO P ON G.CODPROD = P.CODPROD
WHERE G.CODREL = :CODREL
  AND G.CODEMP IN (1, 5)
ORDER BY G.SUGCOMPRA DESC
