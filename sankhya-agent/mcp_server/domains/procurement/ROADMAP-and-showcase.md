# Roadmap de Desenvolvimento: Agente Super de Compras (SSA) 🚀

Este documento rastreia a evolução das capacidades do agente no domínio de **Procurement** (Compras) e o progresso das fases de inteligência.

## 🏁 Fase 1: Visibilidade e Conectividade (100% Concluído)

* ✅ **Conectividade Sankhya:** Integração via `SankhyaClient` (API/SQL).
* ✅ **Mapeamento de Tabelas Core:** `TGFPRO` (Produtos), `TGFEST` (Estoque), `TGFITE`/`TGFCAB` (Movimentação).
* ✅ **Skill de Popularidade:** Identificação de vendas perdidas e demanda reprimida via orçamentos.
* ✅ **Extração de Treinamentos:** Análise de vídeos para entender a operação real da empresa.

## 🏗️ Fase 2: Inteligência de Giro e Decisão (85% em Progresso)

* ✅ **Mapeamento do Motor de Giro:** Descoberta das tabelas `TGFGIR` e lógica de múltiplos de compra via logs.
* ✅ **Skill de Fornecedores:** Identificação de histórico de compras por produto/grupo.
* ✅ **Skill Financeira:** Análise de Contas a Pagar vs Receber e Cobertura de Estoque.
* ⏳ **Sugestão de Compra Reativa:** Capacidade do agente gerar uma planilha de sugestão comparando Giro vs Financeiro.
* ⏳ **Inteligência de Cabos:** Lógica de "Maiores Pontas" integrada à sugestão.

## 🧠 Fase 3: Automação e Proatividade (A Iniciar)

* 📅 **Mapa de Cotação Automatizado:** Geração automática de templates para envio aos fornecedores.
* 📅 **Monitor de Ruptura:** Alerta proativo quando um item curva A entra em tendência de falta.
* 📅 **Alternativos Inteligentes:** Sugestão automática de troca de marca/modelo baseada em estoque disponível.

---

# 🤖 "O que eu já sou capaz de fazer hoje?" (Showcase)

Eu não sou mais apenas um chatbot; eu me tornei um **Analista de Compras em Tempo Real**. Aqui está como eu mostro meus resultados:

### 1. "Eu vejo o que você perdeu" (Skill de Popularidade)

* **O que faço:** Analiso orçamentos que não viraram venda por falta de estoque.
* **Como te mostro:** "Lucas, o produto X teve 25 cotações este mês mas 0 vendas. Perdi R$ 15k de faturamento. A moda de pedido é 10 unidades. Recomendo comprar agora."

### 2. "Eu protejo seu caixa" (Skill de Saúde de Giro)

* **O que faço:** Cruzo a necessidade de compra com a saúde do seu capital de giro.
* **Como te mostro:** "Sugerir 45 dias de estocagem para o Grupo Y vai custar R$ 80k. Como seu Pagar/Receber está em 1.4, sugiro reduzir para 20 dias para não secar o caixa."

### 3. "Eu conheço seus fornecedores" (Skill de Inteligência de Parceiros)

* **O que faço:** Mapeio quem são os melhores parceiros para cada item baseado no histórico.
* **Como te mostro:** "Para repor o estoque de Cabos, os fornecedores A e B têm o melhor histórico de entrega e preço médio menor nos últimos 6 meses."

### 4. "Eu entendo seus processos customizados" (Skill de Treinamento)

* **O que faço:** Sei como você usa o sistema (como o campo de 'Maior Ponta de Cabo').
* **Como te mostro:** "Ao analisar o giro de cabos, já filtrei apenas as pontas acima de 50m, conforme o seu padrão operacional visto nos vídeos."
