# Sankhya API - Documentação Técnica

## Autenticação (Gateway OAuth 2.0)

**Endpoint:** `POST https://api.sankhya.com.br/authenticate`

**Headers:**

- `Content-Type: application/x-www-form-urlencoded`
- `X-Token: {token da aplicação}`

**Body (form-urlencoded):**

- `grant_type=client_credentials`
- `client_id={seu_client_id}`
- `client_secret={seu_client_secret}`

**Resposta:** `{ "access_token": "eyJ...", "expires_in": 3600 }`

O `access_token` (Bearer Token) deve ser enviado em todas as chamadas subsequentes no header `Authorization: Bearer {token}`.

---

## Execução de Queries SQL (DbExplorerSP)

**Endpoint:** `POST https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json`

**Headers:**

- `Authorization: Bearer {access_token}`
- `Content-Type: application/json`

**Body (JSON):**

```json
{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT CODPROD, DESCRPROD FROM TGFPRO WHERE ROWNUM <= 10"
  }
}
```

**Resposta (status=1 = sucesso):**

```json
{
  "status": "1",
  "responseBody": {
    "fieldsMetadata": [
      {"name": "CODPROD", "type": "N"},
      {"name": "DESCRPROD", "type": "S"}
    ],
    "rows": [
      [1, "PRODUTO EXEMPLO"],
      [2, "OUTRO PRODUTO"]
    ]
  }
}
```

> **ATENÇÃO:** `rows` retorna arrays posicionais. Use `fieldsMetadata` para mapear índice → nome da coluna.

---

## Consulta de Registros (CRUDServiceProvider)

### loadRecords (vários registros)

**Endpoint:** `POST .../mge/service.sbr?serviceName=CRUDServiceProvider.loadRecords&outputType=json`

**Body:**

```json
{
  "serviceName": "CRUDServiceProvider.loadRecords",
  "requestBody": {
    "dataSet": {
      "rootEntity": "Parceiro",
      "includePresentationFields": "S",
      "offsetPage": "0",
      "criteria": {
        "expression": {
          "$": "this.CODPARC = 1"
        }
      }
    }
  }
}
```

### loadRecord (registro único)

Mesma estrutura mas com `serviceName=CRUDServiceProvider.loadRecord`.

---

## Endpoints REST do Gateway (APIs Nativas)

### Estoque

- `GET /gateway/v1/estoque/{codProd}` — Estoque de um produto
- `GET /gateway/v1/estoque/locais` — Locais de estoque

### Clientes

- `GET /gateway/v1/clientes` — Lista de clientes
- `POST /gateway/v1/clientes` — Incluir cliente

### Financeiro

- `GET /gateway/v1/financeiros/receitas` — Receitas
- `GET /gateway/v1/financeiros/despesas` — Despesas

### Serviços Especialistas (API Legada via Gateway)

- `POST incluiMovimentos` — Incluir pedidos/notas
- `POST incAltItemMovimento` — Incluir/alterar itens
- `POST cancelaMovimento` — Cancelar movimentos
- `POST faturaMovimento` — Faturar movimentos
- `GET precoproduto` — Consulta de preços

---

## Códigos de Status

- `status: "1"` — Sucesso
- `status: "0"` — Erro (ver `statusMessage`)
- HTTP 401 — Token expirado (re-autenticar)
