# Mapeamento Completo da API Sankhya

> Documento gerado em 10/02/2026 a partir da raspagem da documentação oficial: <https://developer.sankhya.com.br/reference>

---

## Índice

1. [Infraestrutura e URLs Base](#1-infraestrutura-e-urls-base)
2. [Autenticação](#2-autenticação)
3. [API REST (Gateway)](#3-api-rest-gateway)
4. [API Legada (Serviços CRUD/SP)](#4-api-legada-serviços-crudsp)
5. [Serviços Especialistas (API Legada)](#5-serviços-especialistas-api-legada)
6. [Resumo de Capacidades por Módulo](#6-resumo-de-capacidades-por-módulo)

---

## 1. Infraestrutura e URLs Base

| Ambiente   | URL Base                              |
|------------|---------------------------------------|
| Produção   | `https://api.sankhya.com.br/`         |
| Sandbox    | `https://api.sandbox.sankhya.com.br/` |

### Padrão de Requisição via Gateway

Todas as requisições passam pelo Gateway. A URL padrão para serviços é:

```
POST {URL_BASE}/gateway/v1/mge/service.sbr?serviceName={NOME_DO_SERVICO}
```

Headers obrigatórios:

- `Authorization: Bearer {bearerToken}` (legado) ou `Authorization: Bearer {access_token}` (OAuth 2.0)
- `Content-Type: application/json`

---

## 2. Autenticação

### 2.1 OAuth 2.0 (Client Credentials) — RECOMENDADO

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /gateway/v1/auth/authenticate` |
| **Método** | POST |
| **Descrição** | Gera access token JWT para autenticação |

**Parâmetros necessários:**

- `client_id` — fornecido na Área do Desenvolvedor
- `client_secret` — fornecido na Área do Desenvolvedor
- `X-Token` (header) — obtido na tela Configurações Gateway do Sankhya Om

**Retorno:** access_token JWT para uso nas chamadas subsequentes.

---

### 2.2 Login com Usuário e Senha (LEGADO — expira 31/03/2026)

| Campo | Valor |
|-------|-------|
| **Endpoint** | `POST /login` |
| **Método** | POST |
| **Descrição** | Autenticação legada com usuário, senha, appkey e token |

**Fluxo:**

1. `POST /login` → recebe `bearerToken`
2. Chamadas subsequentes usando `Authorization: Bearer {bearerToken}`
3. Logout: `POST /gateway/v1/mge/service.sbr?serviceName=MobileLoginSP.logout`

**Notas:**

- Sessão expira após 30 min de inatividade (configurável via `INATSESSTIMEOUT`)
- Sempre realizar logout ao final

---

## 3. API REST (Gateway)

### 3.1 Cadastros Básicos (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/v1/naturezas` | GET | Lista de Naturezas |
| 2 | `/v1/naturezas/{codigoNatureza}` | GET | Natureza específica |
| 3 | `/v1/centros-resultado` | GET | Lista de Centros de Resultado |
| 4 | `/v1/centros-resultado/{codigoCentroResultado}` | GET | Centro de Resultado específico |
| 5 | `/v1/tipos-operacao` | GET | Lista de Tipos de Operação |
| 6 | `/v1/tipos-operacao/{codigoTipoOperacao}` | GET | Tipo de Operação específico |
| 7 | `/v1/projetos` | GET | Lista de Projetos |
| 8 | `/v1/projetos/{codigoProjeto}` | GET | Projeto específico |
| 9 | `/v1/vendedores` | GET | Lista de Vendedores |
| 10 | `/v1/vendedores/{codigoVendedor}` | GET | Vendedor específico |
| 11 | `/v1/usuarios` | GET | Lista de Usuários |
| 12 | `/v1/usuarios/{codigoUsuario}` | GET | Usuário específico |
| 13 | `/v1/regioes` | GET | Lista de Regiões |
| 14 | `/v1/regioes/{codigoRegiao}` | GET | Região específica |
| 15 | `/v1/cidades` | GET | Lista de Cidades |
| 16 | `/v1/cidades/{codigoCidade}` | GET | Cidade específica |
| 17 | `/v1/logradouros` | GET | Lista de Logradouros |
| 18 | `/v1/logradouros/{codigoLogradouro}` | GET | Logradouro específico |
| 19 | `/v1/bairros` | GET | Lista de Bairros |
| 20 | `/v1/bairros/{codigoBairro}` | GET | Bairro específico |
| 21 | `/v1/veiculos` | GET | Lista de Veículos |
| 22 | `/v1/veiculos/{codigoVeiculo}` | GET | Veículo específico |
| 23 | `/v1/empresas` | GET | Lista de Empresas |
| 24 | `/v1/empresas/{codigoEmpresa}` | GET | Empresa específica |

---

### 3.2 Clientes (CRUD)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/clientes` | GET | Lista de clientes | 🔍 Leitura |
| 2 | `/clientes` | POST | Incluir cliente | ✏️ Inserção |
| 3 | `/clientes/contatos` | POST | Incluir contato do cliente | ✏️ Inserção |
| 4 | `/clientes` | PUT | Atualizar cliente | 🔄 Atualização |
| 5 | `/clientes/contatos` | PUT | Atualizar contato do cliente | 🔄 Atualização |

---

### 3.3 Estoque (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/estoque/produto/{codigoProduto}` | GET | Estoque de um produto |
| 2 | `/estoque/produtos` | GET | Estoque de vários produtos |
| 3 | `/v1/estoque/locais` | GET | Lista de Locais de Estoque |
| 4 | `/v1/estoque/locais/{codigoLocal}` | GET | Local de Estoque específico |

---

### 3.4 Financeiros — Cadastros (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/v1/financeiros/tipos-pagamento` | GET | Lista de Tipos de Pagamento |
| 2 | `/v1/financeiros/tipos-pagamento/{codigo}` | GET | Tipo de Pagamento específico |
| 3 | `/v1/financeiros/moedas` | GET | Lista de Moedas |
| 4 | `/v1/financeiros/moedas/{codigoMoeda}` | GET | Moeda específica |
| 5 | `/v1/financeiros/moedas/{codigoMoeda}/cotacoes` | GET | Lista de Cotações de Moedas |
| 6 | `/v1/financeiros/bandeiras-tef` | GET | Lista de Bandeiras TEF |
| 7 | `/v1/financeiros/redes-tef` | GET | Lista de Redes (Adquirentes) TEF |
| 8 | `/v1/financeiros/contas-bancaria` | GET | Lista de Contas Bancárias |
| 9 | `/v1/financeiros/contas-bancaria/{codigo}` | GET | Conta Bancária específica |

---

### 3.5 Financeiros — Movimentos (CRUD completo)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/financeiros/receitas` | GET | Obter receitas | 🔍 Leitura |
| 2 | `/financeiros/receitas` | POST | Registrar receita | ✏️ Inserção |
| 3 | `/financeiros/receitas` | PUT | Atualizar receita | 🔄 Atualização |
| 4 | `/financeiros/receitas/baixa` | POST | Realizar baixa de receita | ⚡ Ação |
| 5 | `/financeiros/despesas` | GET | Obter despesas | 🔍 Leitura |
| 6 | `/financeiros/despesas` | POST | Registrar despesa | ✏️ Inserção |
| 7 | `/financeiros/despesas` | PUT | Atualizar despesa | 🔄 Atualização |
| 8 | `/financeiros/despesas/baixa` | POST | Realizar baixa de despesa | ⚡ Ação |

---

### 3.6 Fiscal

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/v1/fiscal/servicos-tomados/nfse` | POST | Importar NF de Serviço | ✏️ Inserção |
| 2 | `/v1/fiscal/impostos/calculo` | POST | Calcular impostos em vendas | ⚡ Ação |

---

### 3.7 HCM — Cadastros (somente leitura + admissão)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/v1/pessoal/cargos` | GET | Lista de Cargos | 🔍 |
| 2 | `/v1/pessoal/cargos/{codigoCargo}` | GET | Cargo específico | 🔍 |
| 3 | `/v1/pessoal/sindicatos` | GET | Lista de Sindicatos | 🔍 |
| 4 | `/v1/pessoal/sindicatos/{codigoSindicato}` | GET | Sindicato específico | 🔍 |
| 5 | `/v1/pessoal/funcoes` | GET | Lista de Funções | 🔍 |
| 6 | `/v1/pessoal/funcoes/{codigoFuncao}` | GET | Função específica | 🔍 |
| 7 | `/v1/pessoal/departamentos` | GET | Lista de Departamentos | 🔍 |
| 8 | `/v1/pessoal/departamentos/{codigo}` | GET | Departamento específico | 🔍 |
| 9 | `/v1/pessoal/locais-ponto` | GET | Lista de Locais de Trabalho | 🔍 |
| 10 | `/v1/pessoal/locais-ponto/{codigo}` | GET | Local de Trabalho específico | 🔍 |
| 11 | `/v1/pessoal/identificacao-carga-horaria` | GET | Lista de Cargas Horárias | 🔍 |
| 12 | `/v1/pessoal/identificacao-carga-horaria/{codigo}` | GET | Carga Horária específica | 🔍 |
| 13 | `/v1/pessoal/carga-horaria` | GET | Registro de cargas horárias | 🔍 |
| 14 | `/v1/pessoal/carga-horaria-historica` | GET | Cargas horárias históricas | 🔍 |
| 15 | `/v1/pessoal/historicos-ocorrencia` | GET | Lista de Histórico de Ocorrências | 🔍 |
| 16 | `/v1/pessoal/historicos-ocorrencia/{codigo}` | GET | Histórico específico | 🔍 |
| 17 | `/v1/pessoal/ferias` | GET | Registro de férias | 🔍 |
| 18 | `/v1/pessoal/ocorrencias` | GET | Registro de ocorrências | 🔍 |
| 19 | `/v1/pessoal/movimentos` | GET | Registro de movimentos | 🔍 |
| 20 | `/v1/pessoal/faltas` | GET | Lista de Faltas | 🔍 |
| 21 | `/v1/pessoal/atrasos` | GET | Lista de Atrasos | 🔍 |
| 22 | `/v1/pessoal/empresas` | GET | Lista Empresas (HCM) | 🔍 |
| 23 | `/v1/pessoal/empresas/{codigoEmpresa}` | GET | Empresa específica (HCM) | 🔍 |
| 24 | `/v1/pessoal/tomadores` | GET | Lista de Tomadores | 🔍 |
| 25 | `/v2/funcionarios/admissao` | POST | Criar requisição de admissão | ✏️ |
| 26 | `/v2/funcionarios/admissao/{codigo}` | GET | Detalhes da requisição | 🔍 |

---

### 3.8 HCM — Integrações

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/v1/pessoal/inconsistencias` | GET | Consulta inconsistências de integração |

---

### 3.9 HCM — Funcionários (CRUD)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/v1/funcionarios/admissao` | POST | Criar requisição de admissão | ✏️ |
| 2 | `/v1/funcionarios/admissao/{codigo}` | GET | Detalhes da admissão | 🔍 |
| 3 | `/v1/pessoal/funcionarios` | GET | Lista funcionários modificados | 🔍 |
| 4 | `/v1/pessoal/funcionarios/{codFunc}/empresa/{codEmp}` | GET | Dados completos do funcionário | 🔍 |
| 5 | `.../faltas` | GET | Faltas do funcionário | 🔍 |
| 6 | `.../atrasos` | GET | Atrasos do funcionário | 🔍 |
| 7 | `.../tomadores` | GET | Tomadores do funcionário | 🔍 |
| 8 | `.../carga-horaria-historica` | GET | Cargas horárias históricas | 🔍 |
| 9 | `.../ocorrencias` | GET | Ocorrências do funcionário | 🔍 |
| 10 | `.../ferias` | GET | Férias do funcionário | 🔍 |
| 11 | `.../movimentos` | GET | Movimentos do funcionário | 🔍 |
| 12 | `.../recibos-esocial` | PUT | Atualizar recibos eSocial SST | 🔄 |

---

### 3.10 Logística (CRUD completo)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/motoristas` | GET | Lista de Motoristas | 🔍 |
| 2 | `/motoristas` | POST | Incluir motorista | ✏️ |
| 3 | `/motoristas/{codigo}` | GET | Motorista específico | 🔍 |
| 4 | `/motoristas/{codigo}` | PUT | Atualizar motorista | 🔄 |
| 5 | `/ordens-carga` | GET | Lista de Ordens de Carga | 🔍 |
| 6 | `/ordens-carga` | POST | Incluir Ordem de Carga | ✏️ |
| 7 | `/ordens-carga/{codigo}` | GET | Ordem de Carga específica | 🔍 |
| 8 | `/ordens-carga/{codigo}` | PUT | Atualizar Ordem de Carga | 🔄 |
| 9 | `/ordens-carga/{codigo}/pedidos` | GET | Pedidos da Ordem de Carga | 🔍 |
| 10 | `/ordens-carga/{codigo}/pedidos` | PUT | Adicionar pedidos à OC | 🔄 |
| 11 | `/ordens-carga/{codigo}/pedidos/{pedido}` | PUT | Remover pedido da OC | ❌ |
| 12 | `/transportadoras` | GET | Lista de Transportadoras | 🔍 |
| 13 | `/transportadoras` | POST | Incluir transportadora | ✏️ |
| 14 | `/transportadoras/{codigo}` | GET | Transportadora específica | 🔍 |
| 15 | `/transportadoras/{codigo}` | PUT | Atualizar transportadora | 🔄 |

---

### 3.11 Preços (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/precos/produto/{codProd}/tabela/{codTab}` | GET | Preço por produto e tabela |
| 2 | `/precos/produto/{codProd}` | GET | Preço do produto (todas tabelas) |
| 3 | `/precos/tabela/{codTab}` | GET | Preços vinculados a uma tabela |
| 4 | `/precos/contexto` | POST | Preço contextualizado (com regras) |

---

### 3.12 Produtos (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/v1/produtos` | GET | Lista de Produtos |
| 2 | `/v1/produtos/{codigoProduto}` | GET | Produto específico |
| 3 | `/v1/produtos/{codigoProduto}/componentes` | GET | Componentes do produto |
| 4 | `/v1/produtos/{codigoProduto}/volumes` | GET | Volumes do produto |
| 5 | `/v1/produtos/{codigoProduto}/alternativos` | GET | Produtos alternativos |
| 6 | `/v1/produtos/volumes` | GET | Lista de Volumes |
| 7 | `/v1/produtos/volumes/{codigoVolume}` | GET | Volume específico |
| 8 | `/v1/produtos/grupos` | GET | Lista de Grupos de Produto |
| 9 | `/v1/produtos/grupos/{codigoGrupo}` | GET | Grupo de Produto específico |

---

### 3.13 Vendas — Pedidos (CRUD)

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/pedidos` | GET | Consultar pedidos de venda | 🔍 |
| 2 | `/pedidos` | POST | Incluir pedido de venda | ✏️ |
| 3 | `/pedidos` | PUT | Atualizar pedido de venda | 🔄 |
| 4 | `/pedidos/cancelar` | POST | Cancelar pedido de venda | ❌ |

---

### 3.14 Vendas — CF-e/SAT

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/cfe-sat` | POST | Incluir CF-e | ✏️ |
| 2 | `/cfe-sat/cancelar` | POST | Cancelar CF-e | ❌ |
| 3 | `/cfe-sat/inutilizar` | POST | Inutilizar numeração CF-e | ⚡ |

---

### 3.15 Vendas — NF-e (somente leitura)

| # | Endpoint | Método | Descrição |
|---|----------|--------|-----------|
| 1 | `/nfe` | GET | Consultar lista de NF-e |
| 2 | `/nfe/{codigo}` | GET | Consulta detalhada de NF-e |

---

### 3.16 Vendas — NFC-e

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/nfce` | POST | Incluir NFC-e | ✏️ |
| 2 | `/nfce/autorizar` | POST | Autorizar NFC-e em contingência | ⚡ |
| 3 | `/nfce/cancelar` | POST | Cancelar NFC-e | ❌ |
| 4 | `/nfce/inutilizar` | POST | Inutilizar numeração NFC-e | ⚡ |

---

### 3.17 Vendas — Gestão de Caixa/PDV

| # | Endpoint | Método | Descrição | Operação |
|---|----------|--------|-----------|----------|
| 1 | `/caixa/abrir` | POST | Abertura do Caixa/PDV | ⚡ |
| 2 | `/caixa/aberto` | GET | Buscar caixa aberto | 🔍 |
| 3 | `/caixa/fechar` | POST | Fechamento do Caixa/PDV | ⚡ |
| 4 | `/caixa/sangria` | POST | Registrar sangria | ⚡ |
| 5 | `/caixa/suprimento` | POST | Registrar suprimento | ⚡ |
| 6 | `/caixa/recebimento` (inclusão) | POST | Registrar recebimento (inc.) | ✏️ |
| 7 | `/caixa/recebimento` (baixa) | POST | Registrar recebimento (baixa) | ⚡ |

---

## 4. API Legada (Serviços CRUD/SP)

> Estes serviços são acessados via `POST {URL_BASE}/gateway/v1/mge/service.sbr?serviceName={SERVICO}`

### 4.1 Consulta de Dados

#### `CRUDServiceProvider.loadRecords` — Consulta múltiplos registros (com paginação)

```json
{
  "serviceName": "CRUDServiceProvider.loadRecords",
  "requestBody": {
    "dataSet": {
      "rootEntity": "Produto",
      "ignoreCalculatedFields": "true",
      "useFileBasedPagination": "true",
      "includePresentationFields": "N",
      "tryJoinedFields": "true",
      "modifiedSince": "2024-04-16T12:59:59",
      "offsetPage": "0",
      "criteria": {
        "expression": { "$": "CODPROD IN ( ?, ? )" },
        "parameter": [
          { "$": "1", "type": "I" },
          { "$": "2", "type": "I" }
        ]
      },
      "entity": [
        { "path": "", "fieldset": { "list": "CODPROD, DESCRPROD" } },
        { "path": "GrupoProduto", "fieldset": { "list": "CODGRUPOPROD, DESCRGRUPOPROD" } }
      ]
    }
  }
}
```

**Propriedades importantes:**

| Propriedade | Descrição |
|-------------|-----------|
| `rootEntity` | Nome da entidade a ser consultada |
| `modifiedSince` | Retorna apenas registros alterados após a data (requer logAlteracoesTabelas habilitado) |
| `ignoreCalculatedFields` | `true` = ignora campos calculados (melhor performance) |
| `useFileBasedPagination` | `true` = paginação em disco (para > 1000 páginas) |
| `offsetPage` | Página a retornar (começa em 0). Verificar `hasMoreResult` para próximas páginas |
| `criteria.expression` | Condição WHERE da consulta (usar `?` para parâmetros) |
| `criteria.parameter` | Valores dos parâmetros (tipos: `I`=inteiro, `S`=string, etc.) |
| `entity` | Campos a retornar. `path` = entidade relacionada (join automático) |

#### `CRUDServiceProvider.loadRecord` — Consulta registro único

Similar ao `loadRecords`, mas retorna apenas 1 registro.

#### `loadView` — Consulta sem paginação

Para consultas leves sem necessidade de paginação.

---

### 4.2 Inclusão e Alteração de Dados

#### `DatasetSP.save` — Inserir e Alterar qualquer entidade

**Inclusão (sem `pk`):**

```json
{
  "serviceName": "DatasetSP.save",
  "requestBody": {
    "entityName": "Parceiro",
    "standAlone": false,
    "fields": ["CODPARC", "NOMEPARC", "ATIVO", "TIPPESSOA", "CODCID"],
    "records": [{
      "values": {
        "1": "NOME DO PARCEIRO",
        "2": "S",
        "3": "F",
        "4": "1"
      }
    }]
  }
}
```

**Atualização (com `pk`):**

```json
{
  "serviceName": "DatasetSP.save",
  "requestBody": {
    "entityName": "Parceiro",
    "standAlone": false,
    "fields": ["CODPARC", "NOMEPARC", "ATIVO"],
    "records": [{
      "pk": { "CODPARC": "4454" },
      "values": { "1": "JOSE DA SILVA XAVIER" }
    }]
  }
}
```

**Inclusão com FK (registros filhos):**

```json
{
  "serviceName": "DatasetSP.save",
  "requestBody": {
    "entityName": "Contato",
    "standAlone": false,
    "fields": ["CODCONTATO", "ATIVO", "NOMECONTATO", "EMAIL", "CELULAR"],
    "records": [{
      "foreignKey": { "CODPARC": "4454" },
      "values": {
        "1": "S",
        "2": "Nome do Contato",
        "4": "33 999998888"
      }
    }]
  }
}
```

> ⚠️ A numeração dos `values` segue a posição do campo no array `fields` (começando em 0 para a PK, 1 para o segundo campo, etc.)

---

### 4.3 Log de Alterações

#### `logAlteracoesTabelas` — Histórico de Alterações

Consulta o log de alterações de tabelas para sincronização incremental.

---

## 5. Serviços Especialistas (API Legada)

Serviços com regras de negócio específicas do ERP:

### 5.1 Movimentos (Pedidos, Notas, etc.)

#### `CACSP.incluirNota` — Incluir Movimento

```json
{
  "serviceName": "CACSP.incluirNota",
  "requestBody": {
    "nota": {
      "cabecalho": {
        "NUNOTA": {},
        "CODPARC": { "$": "1" },
        "DTNEG": { "$": "09/12/2022" },
        "CODTIPOPER": { "$": "2000" },
        "CODTIPVENDA": { "$": "12" },
        "CODVEND": { "$": "0" },
        "CODEMP": { "$": "1" },
        "TIPMOV": { "$": "O" }
      },
      "itens": {
        "INFORMARPRECO": "True",
        "item": [{
          "NUNOTA": {},
          "CODPROD": { "$": "8" },
          "QTDNEG": { "$": "1" },
          "CODLOCALORIG": { "$": "0" },
          "CODVOL": { "$": "UN" },
          "VLRUNIT": { "$": "1.75" },
          "PERCDESC": { "$": "0" }
        }]
      }
    }
  }
}
```

**Campos obrigatórios do cabeçalho:**

- `NUNOTA` — Número Único da nota (vazio para inclusão)
- `CODPARC` — Código do Parceiro
- `DTNEG` — Data de Negociação
- `CODTIPOPER` — Código do Tipo de Operação
- `CODTIPVENDA` — Tipo de Negociação
- `CODVEND` — Código do Vendedor
- `CODEMP` — Código da Empresa
- `TIPMOV` — Tipo de Movimento

**Campos obrigatórios dos itens:**

- `CODPROD` — Código do Produto
- `QTDNEG` — Quantidade
- `CODLOCALORIG` — Código Local de Origem
- `CODVOL` — Código do Volume

**Campos condicionais (quando `INFORMARPRECO = True`):**

- `VLRUNIT` — Valor Unitário
- `PERCDESC` — Percentual de Desconto

### 5.2 Outros Serviços Especialistas

| # | Serviço | Método | Descrição |
|---|---------|--------|-----------|
| 1 | `CACSP.incluirNota` | POST | Incluir movimentos (pedidos, notas) |
| 2 | Incluir/Alterar itens de movimentos | POST | Manipular itens de um movimento existente |
| 3 | Excluir itens de movimentos | POST | Remover itens de um movimento |
| 4 | Cancelamento de movimentos | POST | Cancelar um movimento inteiro |
| 5 | Faturamento de movimentos | POST | Faturar um movimento |
| 6 | Consulta de Preços | GET | Consultar preço de produto |
| 7 | Anexar Arquivos | GET | Anexar arquivos a registros |

---

## 6. Resumo de Capacidades por Módulo

| Módulo | Leitura | Inserção | Atualização | Exclusão/Cancelamento | Total Endpoints |
|--------|---------|----------|-------------|----------------------|-----------------|
| **Cadastros Básicos** | ✅ 24 | ❌ | ❌ | ❌ | 24 |
| **Clientes** | ✅ 1 | ✅ 2 | ✅ 2 | ❌ | 5 |
| **Estoque** | ✅ 4 | ❌ | ❌ | ❌ | 4 |
| **Financeiros Cadastros** | ✅ 9 | ❌ | ❌ | ❌ | 9 |
| **Financeiros Movimentos** | ✅ 2 | ✅ 2 | ✅ 2 | ❌ (baixa: 2) | 8 |
| **Fiscal** | ❌ | ✅ 1 | ❌ | ❌ | 2 |
| **HCM Cadastros** | ✅ 24 | ✅ 1 | ❌ | ❌ | 26 |
| **HCM Integrações** | ✅ 1 | ❌ | ❌ | ❌ | 1 |
| **HCM Funcionários** | ✅ 9 | ✅ 1 | ✅ 1 | ❌ | 12 |
| **Logística** | ✅ 5 | ✅ 3 | ✅ 4 | ✅ 1 | 15 |
| **Preços** | ✅ 3 | ❌ | ❌ | ❌ | 4 |
| **Produtos** | ✅ 9 | ❌ | ❌ | ❌ | 9 |
| **Vendas Pedidos** | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 | 4 |
| **Vendas CF-e/SAT** | ❌ | ✅ 1 | ❌ | ✅ 2 | 3 |
| **Vendas NF-e** | ✅ 2 | ❌ | ❌ | ❌ | 2 |
| **Vendas NFC-e** | ❌ | ✅ 1 | ❌ | ✅ 3 | 4 |
| **Vendas Gestão Caixa** | ✅ 1 | ✅ 1 | ❌ | ❌ | 7 |
| **API Legada — CRUD** | ✅ ∞ | ✅ ∞ | ✅ ∞ | ❌ | Genérico |
| **API Legada — Especialista** | ✅ 2 | ✅ 3 | ❌ | ✅ 2 | 7 |
| **TOTAL** | — | — | — | — | **~146+** |

---

## Apêndice: API Legada vs API REST

| Aspecto | API REST (Gateway) | API Legada (Serviços) |
|---------|-------------------|----------------------|
| **Padrão** | RESTful (endpoints específicos) | Genérico (serviceName) |
| **Vantagem** | Mais simples, tipada, documentada | Acesso a QUALQUER entidade |
| **Autenticação** | OAuth 2.0 recomendado | Ambos suportados |
| **Paginação** | Via query params | Via `offsetPage` + `hasMoreResult` |
| **Joins** | Automáticos nos endpoints | Manual via `entity.path` |
| **Flexibilidade** | Limitada aos endpoints documentados | Total (qualquer entidade/campo) |
| **Uso recomendado** | Operações padronizadas | Consultas customizadas, operações sem endpoint REST |

> **Nota:** A API Legada através de `CRUDServiceProvider.loadRecords` e `DatasetSP.save` permite acessar **QUALQUER entidade** do Sankhya Om, mesmo aquelas sem endpoint REST dedicado. É a forma mais flexível de integração, porém requer conhecimento do [Dicionário de Dados](https://ajuda.sankhya.com.br/hc/pt-br/articles/360044597294-Dicionário-de-Dados).

---

## Links de Referência

- [Documentação Oficial](https://developer.sankhya.com.br/reference)
- [Guia de Integração](https://developer.sankhya.com.br/reference/guia-integracao)
- [Portal do Desenvolvedor](https://areadev.sankhya.com.br/)
- [Dicionário de Dados](https://ajuda.sankhya.com.br/hc/pt-br/articles/360044597294-Dicionário-de-Dados)
- [Comunidade](https://community.sankhya.com.br/developers)
- [Boas Práticas](https://developer.sankhya.com.br/reference/boas-práticas-para-integração)
- [Códigos de Retorno](https://developer.sankhya.com.br/reference/códigos-de-retorno-da-api)
- [FAQ](https://developer.sankhya.com.br/reference/faq-1)
