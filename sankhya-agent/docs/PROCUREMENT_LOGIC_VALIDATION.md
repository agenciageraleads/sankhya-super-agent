# Validação de Lógica de Compras Híbrida (Sistema + Agente)

Este documento descreve o método matemático proposto para o Agente de Compras. O objetivo é validar se as regras de negócio refletem a estratégia da empresa antes de automatizarmos o processo via WhatsApp.

---

## 1. Glossário e Fontes de Dados

| Termo | Fonte (Sankhya) | Definição |
| :--- | :--- | :--- |
| **Giro Diário** | `TGFGIR.GIRODIARIO` | Média de vendas diárias calculada pelo ERP (suporta sazonalidade parametrizada). |
| **Estoque** | `TGFGIR.ESTOQUE` | Soma do estoque físico da Empresa 1 (Matriz) + Empresa 5 (Filial). |
| **Lead Time** | `TGFGIR.LEADTIME` | Tempo (em dias) que o fornecedor leva para entregar, cadastrado no produto/parceiro. |
| **Sugestão Sistema** | `TGFGIR.SUGCOMPRA` | Quantidade que o Sankhya calculou baseada no Estoque Mínimo/Máximo cadastrado. |
| **Cobertura (Dias)** | Cálculo Agente | `Estoque Atual / Giro Diário`. Se Giro Zero, Cobertura = Infinita. |

---

## 2. A Lógica Híbrida (Agente como Auditor)

O Agente não descarta o Sankhya, mas atua como um **Auditor** que bloqueia excessos ou alerta faltas graves que o sistema ignorou (por erro de parâmetro).

### Cenário A: O "Policial" (Trava de Excesso)

**Problema:** O Sankhya pede compra (ex: por Estoque Mínimo mal cadastrado), mas o produto tem estoque para meses.
**Regra Proposta:**

- **SE** `Cobetura (Dias) > 120` (4 Meses)
- **ENTÃO** `Sugestão Otimizada = 0` (ZERA a compra).
- **Ação:** LIQUIDAR / PROMOÇÃO.

> **Pergunta para Validação:** 120 dias é o limite correto para considerar "Excesso"? Ou deveria ser 90? 180?

### Cenário B: O "Bombeiro" (Prevenção de Ruptura)

**Problema:** O Sankhya diz "Comprar 0", mas o estoque está perigosamente baixo para o tempo de reposição.
**Regra Proposta:**

- **SE** `Cobertura (Dias) < Lead Time`
- **E** `Sugestão Sistema == 0`
- **ENTÃO** O Agente calcula: `Necessidade = (Giro Diário * (Lead Time * 1.3)) - Estoque Atual`.
- *Nota:* O fator `1.3` adiciona uma margem de segurança de 30% sobre o tempo de entrega.

> **Pergunta para Validação:** A margem de segurança de 30% é adequada?

### Cenário C: A "Zona de Confiança"

**Situação:** A cobertura não é nem excessiva (>120) nem crítica (< Lead Time).
**Regra Proposta:**

- Aceitar a `Sugestão Sistema` integralmente.

---

## 3. Simulações Práticas

Para garantir que estamos na mesma página, veja como o Robô agiria nestes casos:

### Caso 1: O "Falso Mínimo"

* **Produto:** Conector Curva
- **Estoque:** 100 un
- **Giro:** 0,5 un/dia (Cobertura = 200 dias)
- **Sankhya Pede:** 50 un (Porque alguém cadastrou Mínimo 150)
- --------------
- **Decisão Agente:** **COMPRAR 0**. (Motivo: Cobertura 200d > Teto 120d).
- *Sem essa regra, você compraria item para ficar parado 1 ano.*

### Caso 2: A "Emergência Invisível"

* **Produto:** Eletroduto PVC
- **Estoque:** 10 un
- **Giro:** 5 un/dia (Cobertura = 2 dias)
- **Lead Time:** 7 dias
- **Sankhya Pede:** 0 un (Talvez parâmetro errado ou pedido pendente não considerado)
- --------------
- **Decisão Agente:** **COMPRAR 35**.
- *Conta:* `(5 giro * (7 lead * 1.3 margem)) - 10 estoque = 45.5 - 10 = 35.5`.
- *O Agente salva a ruptura iminente antes de acontecer.*

---

## 4. O que precisamos da sua aprovação?

1. [ ] O limite de **120 dias** para considerar "Excesso" está bom?
2. [ ] A margem de segurança de **30%** no cálculo de ruptura está ok?
3. [ ] Concorda em manter a sugestão do Sankhya nos casos intermediários?
