import json
import os
import requests
from gtts import gTTS
import time
import io
import base64

# --- CONFIGURAÇÕES ---
# Altere estas variáveis de acordo com sua necessidade
ARQUIVO_ENTRADA = "frases.txt"
DECK_NOME = "Spanish" # O nome exato do baralho no Anki
MODELO_NOME = "Basic" # O nome do tipo de nota (geralmente "Básico")
LIMITE_CARDS = 10  # Quantos cards adicionar por execução
IDIOMA_AUDIO = 'es' # Idioma do áudio a ser gerado (ex: 'es' para espanhol)

# URL do AnkiConnect (geralmente não precisa mudar)
ANKI_CONNECT_URL = "http://localhost:8765"

def invoke_anki_connect(action, **params):
    """Função para fazer uma requisição à API do AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload)
        response.raise_for_status()  # Lança um erro para respostas HTTP ruins (4xx ou 5xx)
        response_json = response.json()
        if 'error' in response_json and response_json['error'] is not None:
            print(f"Erro recebido do AnkiConnect: {response_json['error']}")
            return None
        return response_json['result']
    except requests.exceptions.RequestException as e:
        print(f"Não foi possível conectar ao AnkiConnect. Verifique se o Anki está aberto e o plugin AnkiConnect está instalado. Erro: {e}")
        return None

def main():
    """Função principal que orquestra a criação de cards."""
    print("Iniciando script para adicionar cards ao Anki...")

    # 1. Verificar se o Anki está acessível
    if invoke_anki_connect('deckNames') is None:
        return # A mensagem de erro já foi impressa pela função invoke

    # 2. Ler o arquivo de frases
    try:
        with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            linhas = [linha.strip() for linha in f if linha.strip() and '|' in linha]
    except FileNotFoundError:
        print(f"Erro: Arquivo '{ARQUIVO_ENTRADA}' não encontrado. Crie este arquivo no mesmo diretório do script.")
        return

    cards_adicionados = 0
    for i, linha in enumerate(linhas):
        if cards_adicionados >= LIMITE_CARDS:
            print(f"\nLimite de {LIMITE_CARDS} cards atingido. Encerrando.")
            break

        frente, verso = [parte.strip() for parte in linha.split('|', 1)]
        
        print(f"\nProcessando card {cards_adicionados + 1}/{LIMITE_CARDS}: '{frente}'")

        # 4. Verificar se o card já existe para não criar duplicatas
        query = f'"deck:{DECK_NOME}" "Frente:{frente}"'
        if invoke_anki_connect('findNotes', query=query):
            print(f"Card para '{frente}' já existe. Pulando.")
            continue

        # 5. Gerar e armazenar áudio
        nome_arquivo_audio = f"auto_anki_{int(time.time() * 1000)}.mp3"
        try:
            tts = gTTS(text=frente, lang=IDIOMA_AUDIO)
            
            # Criar um stream de bytes em memória para salvar o áudio
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0) # Voltar para o início do stream

            # Ler os bytes e codificar em Base64
            audio_bytes = mp3_fp.read()
            audio_data_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            if invoke_anki_connect('storeMediaFile', filename=nome_arquivo_audio, data=audio_data_b64) is None:
                print("Falha ao armazenar o arquivo de áudio. Pulando este card.")
                continue
            print(f"Áudio '{nome_arquivo_audio}' gerado e armazenado.")
        except Exception as e:
            print(f"Erro ao gerar áudio para '{frente}': {e}")
            continue

        # 6. Montar e adicionar a nota
        campo_frente_com_audio = f"{frente} [sound:{nome_arquivo_audio}]"
        nota = {
            "deckName": DECK_NOME,
            "modelName": MODELO_NOME,
            "fields": {"Front": campo_frente_com_audio, "Back": verso},
            "tags": ["auto-gerado"]
        }

        if invoke_anki_connect('addNote', note=nota):
            print(f"Card para '{frente}' adicionado com sucesso!")
            cards_adicionados += 1
        else:
            print(f"Falha ao adicionar o card para '{frente}'.")

    print(f"\nProcesso concluído. Total de cards adicionados: {cards_adicionados}.")

if __name__ == "__main__":
    main()