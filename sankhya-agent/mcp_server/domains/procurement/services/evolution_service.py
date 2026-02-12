import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("procurement-evolution-service")

class EvolutionService:
    """
    Integração com a Evolution API para comunicação via WhatsApp.
    """

    def __init__(self):
        self.base_url = os.getenv("EVOLUTION_API_URL")
        self.api_key = os.getenv("EVOLUTION_API_TOKEN")
        self.instance = os.getenv("EVOLUTION_INSTANCE_NAME")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def send_text(self, number: str, text: str) -> bool:
        """Envia mensagem de texto."""
        if not self.base_url or not self.instance:
            logger.error("Configurações da Evolution API ausentes.")
            return False

        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": number,
            "text": text,
            "linkPreview": False
        }

        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            return False

    def send_media(self, number: str, media_url: str, caption: str = "", media_type: str = "document") -> bool:
        """Envia mídia (PDF, Imagem, Áudio)."""
        url = f"{self.base_url}/message/sendMedia/{self.instance}"
        payload = {
            "number": number,
            "mediaMessage": {
                "mediatype": media_type,
                "media": media_url,
                "caption": caption
            }
        }

        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=20)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mídia WhatsApp: {e}")
            return False
            
    def get_messages(self, number: str) -> list:
        """Busca mensagens recebidas (Polling fallback se webhook não estiver pronto)."""
        # Endpoint varia conforme versão da Evolution API
        url = f"{self.base_url}/chat/fetchMessages/{self.instance}"
        # ... lógica de filtro simplificada
        return []
