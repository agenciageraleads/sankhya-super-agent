# Plano de Implementação: Auxiliar de Compras (Sankhya Super Agente)

> **Status:** Draft (Baseado no Mapa Operacional do Quadro Branco)
> **Objetivo:** Adicionar a skill de "Analista de Compras" ao Super Agente, permitindo gerenciamento proativo de estoque, cotações e o ciclo completo de NFe/Logística.

## 1. Visão Geral

O módulo "Auxiliar de Compras" transformará o comportamento reativo do agente em **proativo**. Ele monitorará o giro, gerenciará compras casadas, rastreará NFes e conduzirá negociações via WhatsApp (Evolution API), focando no princípio de **Pareto 80/20** e aprendendo com materiais de treinamento multimidia.

---

## 2. Estrutura de Domínio e Treinamento

A arquitetura foi desenhada para separar o currículo de treinamento da lógica de sistema:

```
sankhya-agent/
├── mcp_server/
│   ├── domains/
│   │   ├── procurement/
│   │   │   ├── rules/          <-- Particularidades (SQLs, Yaml)
│   │   │   ├── workflows/      <-- Lógica dos Fluxos (Radar, etc)
│   │   │   ├── training/       <-- REPOSITÓRIO DE CONHECIMENTO (Fotos, Vídeos, Slides)
│   │   │   │   ├── photos/     <-- Quadros brancos, fluxogramas, fotos de produtos
│   │   │   │   ├── videos/     <-- Gravações de tela, treinamentos operacionais
│   │   │   │   ├── slides/     <-- Apresentações de estratégia comercial
│   │   │   │   └── docs/       <-- PDFs de políticas e manuais
│   │   │   └── services/       <-- Adapters (Sankhya, EvolutionAPI)
```

---

## 3. Arquitetura de Processos (Workflows)

O sistema operará nos 4 fluxos vitais do quadro branco:

### 🔄 Fluxo A: Monitoramento (Giro e Reposição)

* **LG (Lista Geral) -> LP (Liberação de Pedido)**.
* Monitora o Giro (`TGFGIR`) e Popularidade (Orçamentos Perdidos).
* Foco em **Pareto (80/20)**.

### ⚡ Fluxo B: Compra Casada (Venda -> Inpanner)

* **Trigger:** Venda realizada sem estoque físico.
* **Ação:** Vincular pedido de compra, rastrear faturamento do fornecedor.

### 🚚 Fluxo C: Acompanhamento (Rastreamento e Logística)

* **ANFe (Acompanhamento NFe) -> Entrega**.
* Rastrear emissão de NFe e status do transporte.

### 📥 Fluxo D: Lançamento e Cadastro (Administrativo)

* **RP? (Recebimento) -> EP (Entrada de Produto)**.
* Pré-lançamento de NFe e atualização de custos/preços.

---

## 4. Releases de Entrega

### 🔍 Fase 0: Discovery & Ingestão (Imediata)

* [ ] **Ingestão Multimídia**: Agente analisa materiais em `training/` para absorver processos.
* [ ] **Mapeamento de BI**: Localizar no Sankhya as queries da "Lista Geral".
* [ ] **Setup Evolution API**: Conectar ao WhatsApp.

### 🟢 Release 1: O "Analista" e Gestor de Cadastro

**Entrega:** Monitoramento 80/20 e atualização de custos.

### 🟡 Release 2: O "Comunicador" e Compra Casada

**Entrega:** Negociação WhatsApp e vínculo de pedidos.

### 🔴 Release 3: O "Logístico" e Fiscal

**Entrega:** Ciclo de NFe e rastreamento.

---

## 5. Próximos Passos (Imediato)

1. **Usuário**: Colocar arquivos em `sankhya-agent/mcp_server/domains/procurement/training/`.
2. **Agente**: Continuar tentando localizar o SQL do BI no banco de dados.

---
*Plano atualizado para incluir Repositório de Treinamento Multimídia.*
