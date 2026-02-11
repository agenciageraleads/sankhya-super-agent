import os
import requests
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sankhya-gateway")

# Logger de auditoria dedicado para rastrear todas as queries SQL executadas
audit_logger = logging.getLogger("sankhya-audit")
_audit_handler = logging.FileHandler(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "activity.log"),
    encoding="utf-8"
)
_audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
audit_logger.addHandler(_audit_handler)
audit_logger.setLevel(logging.INFO)


def format_as_markdown_table(data: List[Dict[str, Any]]) -> str:
    """Converte uma lista de dicionários em uma tabela Markdown formatada."""
    if not data:
        return "_Nenhum registro encontrado._"

    headers = list(data[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_rows = []
    for row in data:
        cells = [str(row.get(h, "")) for h in headers]
        body_rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_row, separator] + body_rows)


class SankhyaGatewayClient:
    """Cliente para o Gateway Sankhya com autenticação OAuth 2.0 + X-Token."""

    def __init__(self):
        self.base_url = os.getenv("SANKHYA_API_URL", "https://api.sankhya.com.br")
        self.client_id = os.getenv("SANKHYA_CLIENT_ID")
        self.client_secret = os.getenv("SANKHYA_CLIENT_SECRET")
        self.x_token = os.getenv("SANKHYA_X_TOKEN")

        self.bearer_token: Optional[str] = None
        self.token_expires_at: float = 0

    def authenticate(self) -> bool:
        """Autentica no Gateway Sankhya via OAuth 2.0 + X-Token."""
        if self.bearer_token and time.time() < self.token_expires_at:
            return True

        logger.info("Autenticando no Gateway Sankhya...")

        url = f"{self.base_url}/authenticate"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Token": self.x_token
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=15)
            response.raise_for_status()
            res_data = response.json()

            # O Sankhya pode retornar 'access_token' ou 'bearerToken'
            self.bearer_token = res_data.get("access_token") or res_data.get("bearerToken")
            expires_in = res_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + float(expires_in) - 60  # margem de 1 min

            if self.bearer_token:
                logger.info("Autenticação via Gateway realizada com sucesso.")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro na autenticação Gateway: {str(e)}")
            return False

    def _get_auth_headers(self) -> Dict[str, str]:
        """Retorna os headers com o Bearer token corrente."""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Executa uma query SQL via DbExplorerSP no Gateway."""
        if not self.authenticate():
            raise Exception("Falha na autenticação com o Gateway Sankhya.")

        # Registra no log de auditoria
        audit_logger.info(f"SQL | {sql.strip()}")

        url = f"{self.base_url}/gateway/v1/mge/service.sbr"
        params = {
            "serviceName": "DbExplorerSP.executeQuery",
            "outputType": "json"
        }
        payload = {
            "serviceName": "DbExplorerSP.executeQuery",
            "requestBody": {
                "sql": sql.strip()
            }
        }

        try:
            response = requests.post(
                url, json=payload, headers=self._get_auth_headers(),
                params=params, timeout=30
            )

            # Re-autenticação automática se token expirou mid-request
            if response.status_code == 401:
                logger.info("Token expirado durante request. Re-autenticando...")
                self.bearer_token = None
                if self.authenticate():
                    response = requests.post(
                        url, json=payload, headers=self._get_auth_headers(),
                        params=params, timeout=30
                    )

            response.raise_for_status()
            res_data = response.json()

            if res_data.get("status") == "1":
                body = res_data.get("responseBody", {})
                fields = body.get("fieldsMetadata", [])
                rows = body.get("rows", [])

                if not rows:
                    return []

                # Mapeia linhas (arrays) para dicionários usando metadados das colunas
                result = []
                for row in rows:
                    item = {}
                    for i, field in enumerate(fields):
                        item[field["name"]] = row[i]
                    result.append(item)
                return result
            else:
                error_msg = res_data.get("statusMessage", "Erro na execução da query")
                logger.error(f"Erro SQL Sankhya: {error_msg}")
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Erro na chamada do DbExplorerSP: {str(e)}")
            raise

    def call_service(self, service_name: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Chamada genérica de serviço via Gateway (JSON)."""
        if not self.authenticate():
            raise Exception("Falha na autenticação com o Gateway Sankhya.")

        audit_logger.info(f"SERVICE | {service_name}")

        url = f"{self.base_url}/gateway/v1/mge/service.sbr"
        params = {
            "serviceName": service_name,
            "outputType": "json"
        }
        payload = {
            "serviceName": service_name,
            "requestBody": request_body
        }

        try:
            response = requests.post(
                url, json=payload, headers=self._get_auth_headers(),
                params=params, timeout=30
            )

            # Re-autenticação automática
            if response.status_code == 401:
                self.bearer_token = None
                if self.authenticate():
                    response = requests.post(
                        url, json=payload, headers=self._get_auth_headers(),
                        params=params, timeout=30
                    )

            response.raise_for_status()
            data = response.json()
            
            # O Sankhya retorna status "0" para erro e "1" para sucesso
            if str(data.get("status", "1")) == "0":
                error_msg = data.get("statusMessage", "Erro desconhecido na API Sankhya")
                # Decodifica escapes se necessário (em alguns casos vem em base64, mas o texto plano é comum)
                raise Exception(f"Erro Funcional Sankhya: {error_msg}")
                
            return data
        except Exception as e:
            # logger.error(f"Erro no serviço {service_name}: {str(e)}") # Já será logado pelo chamador ou audit
            raise
# Instância global para ser usada pelas ferramentas e skills
sankhya = SankhyaGatewayClient()
