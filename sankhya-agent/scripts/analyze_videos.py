import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# List of videos to analyze (Sanitized names)
training_videos = [
    "Monitoramento_Giro.mov",
    "Mapa_de_Cotacao_1.mov",
    "Portal_de_Compras.mov",
    "Alterando_a_Qtd_de_Multiplo_de_Compra_Produtos.mov",
    "Mapa_de_Cotacao_2_Planilha_Compras.mov",
    "Monitoramento_Produtos_Distribuidores_01.mov",
    "Monitoramento_Produtos_Distribuidores_02.mov",
    "Tela_Cadastro_de_Produtos.mov"
]

video_path_base = "/Users/Lucas-Lenovo/Sankhya-Super-Agente/sankhya-agent/mcp_server/domains/procurement/training"
output_path = os.path.join(video_path_base, "video_summaries.md")

# Check existing summaries to avoid duplication
existing_summaries = ""
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        existing_summaries = f.read()

with open(output_path, "a", encoding="utf-8") as out:
    if not existing_summaries:
        out.write("# Resumo dos Treinamentos em Vídeo (Foco SANKHYA)\n\n")
        out.write("> **Nota:** Processos do sistema antigo C&S/Gestor estão sendo ignorados conforme diretriz do usuário.\n\n")

    for video_name in training_videos:
        if f"## {video_name}" in existing_summaries:
            print(f"Skipping {video_name}, already analyzed.")
            continue

        video_path = os.path.join(video_path_base, video_name)
        if not os.path.exists(video_path):
            print(f"Skipping {video_name}, not found.")
            continue

        print(f"Uploading {video_name}...")
        # Uploading with sanitized filename
        file = client.files.upload(file=video_path)
        
        while file.state.name == "PROCESSING":
            print(f"Processing {video_name}...")
            time.sleep(20)
            file = client.files.get(name=file.name)
        
        if file.state.name == "FAILED":
            print(f"Video {video_name} failed to process.")
            continue

        prompt = """
        Você é um Assistente de Implantação de IA expert em Sankhya. 
        ⚠️ REGRA CRÍTICA: Ignore qualquer menção ou tela do sistema antigo C&S (Gestor Antigo). 
        O objetivo é extrair o conhecimento operativo apenas para o SANKHYA.
        
        Analise este vídeo de treinamento e:
        1. Identifique os passos exatos realizados na interface do SANKHYA.
        2. Liste filtros, parâmetros e caminhos (ex: Comercial > Compras > ...).
        3. Explique a lógica de decisão do comprador demonstrada.
        4. Identifique nomes de tabelas (TGF...) ou campos customizados que apareçam.
        Responda em Português (Brasil) de forma técnica e detalhada.
        """
        
        print(f"Analyzing {video_name}...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        
        out.write(f"## {video_name}\n\n")
        out.write(response.text)
        out.write("\n\n---\n\n")
        out.write(f"\n<!-- Finalizado análise de {video_name} em {time.strftime('%Y-%m-%d %H:%M:%S')} -->\n\n")
        out.flush()
        print(f"Done analyzing {video_name}")

print("Análise de vídeos Sankhya concluída.")
