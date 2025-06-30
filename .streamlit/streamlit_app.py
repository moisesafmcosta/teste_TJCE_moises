import streamlit as st
import anthropic
import os
import re
from PIL import Image
import time
import json
import streamlit.components.v1 as components
import speech_recognition as sr
from pathlib import Path # para percorrer diretórios
from pypdf import PdfReader
claude_api_key = os.getenv("CLAUDE_API_KEY")  

if not claude_api_key:
    st.error("Chave CLAUDE_API_KEY não configurada no servidor.")
    st.stop()

# Configurações iniciais
st.set_page_config(
    page_title=" CoJudi",
    page_icon="🏛️",
    layout="wide",
)

st.markdown(
    "<h1 style='text-align:center; margin-top:0'>CoJudi</h1>",
    unsafe_allow_html=True
)

_PADROES = [
    r"de acordo com as informações[^.]*\.?\s*",
    r"de acordo com o guia[^.]*\.?\s*",
    r"conforme (o|a) material[^.]*\.?\s*"
]

# CSS personalizado para estilizar o balão de upload e o aviso

st.markdown(
    """
    <style>

/* Esconde os elementos indesejados */
    ._link_gzau3_10, ._profileContainer_gzau3_53 {
        display: none !important;
        visibility: hidden !important;
    }

        /* Remover barra inferior completa */
        footer {
            visibility: hidden !important;
            display: none !important;
        }

        /* Remover qualquer iframe que possa conter o branding */
        iframe[title="streamlit branding"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Remover a toolbar do Streamlit */
        [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Remover qualquer div fixa que possa conter os botões */
        div[data-testid="stActionButtonIcon"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Ocultar qualquer elemento fixo no canto inferior direito */
        div[style*="position: fixed"][style*="right: 0px"][style*="bottom: 0px"] {
            display: none !important;
            visibility: hidden !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
        /* Remover botões no canto inferior direito */
        iframe[title="streamlit branding"] {
            display: none !important;
        }
       
        footer {
            display: none !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Tentar esconder qualquer outro elemento fixo */
        div[style*="position: fixed"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>

/* Remover barra superior do Streamlit */
header {visibility: hidden;}

/* Remover botão de configurações */
[data-testid="stToolbar"] {visibility: hidden !important;}

/* Remover rodapé do Streamlit */
footer {visibility: hidden;}

/* Remover botão de compartilhamento */
[data-testid="stActionButtonIcon"] {display: none !important;}

/* Ajustar margem para evitar espaços vazios */
.block-container {padding-top: 1rem;}

 .overlay {
            position: fixed;
            bottom: 0;
            right: 0;
            width: 150px;
            height: 50px;
            background-color: white;
            z-index: 1000;
        }

    /* Estilo para o texto na sidebar */
    .stSidebar .stMarkdown, .stSidebar .stTextInput, .stSidebar .stTextArea, .stSidebar .stButton, .stSidebar .stExpander {
        color: white !important;  /* Cor do texto na sidebar */
    }

    /* Estilo para o texto na parte principal */
    .stMarkdown, .stTextInput, .stTextArea, .stButton, .stExpander {
        color: black !important;  /* Cor do texto na parte principal */
    }

    /* Estilo para o container de upload de arquivos */
    .stFileUploader > div > div {
        background-color: white;  /* Fundo branco */
        color: black;  /* Texto preto */
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #ccc;  /* Borda cinza para destacar */
    }

    /* Estilo para o texto dentro do balão de upload */
    .stFileUploader label {
        color: black !important;  /* Texto preto */
    }

    /* Estilo para o botão de upload */
    .stFileUploader button {
        background-color: #8dc50b;  /* Verde */
        color: white;  /* Texto branco */
        border-radius: 5px;
        border: none;
        padding: 8px 16px;
    }

    /* Estilo para o texto de drag and drop */
    .stFileUploader div[data-testid="stFileUploaderDropzone"] {
        color: black !important;  /* Texto preto */
    }

    /* Estilo para o container de avisos (st.warning) */
    div[data-testid="stNotification"] > div > div {
        background-color: white !important;  /* Fundo branco */
        color: black !important;  /* Texto preto */
        border-radius: 10px !important;
        padding: 10px !important;
        border: 1px solid #ccc !important;  /* Borda cinza para destacar */
    }

    /* Estilo para o ícone de aviso */
    div[data-testid="stNotification"] > div > div > div:first-child {
        color: #8dc50b !important;  /* Cor do ícone (verde) */
    }

    /* Estilo para o subtítulo */
    .subtitulo {
        font-size: 16px !important;  /* Tamanho da fonte reduzido */
        color: black !important;  /* Cor do texto alterada para preto */
    }

    /* Estilo para o rótulo do campo de entrada na sidebar */
    .stSidebar label {
        color: white !important;  /* Cor do texto branco */
    }

    /* Estilo para o texto na caixa de entrada do chat */
    .stChatInput input {
        color: white !important;  /* Cor do texto branco */
    }

    /* Estilo para o placeholder na caixa de entrada do chat */
    .stChatInput input::placeholder {
        color: white !important;  /* Cor do placeholder branco */
    }

    /* Estilo para o texto na caixa de entrada do chat */
div.stChatInput textarea {
    color: white !important;  /* Cor do texto branco */
}

/* Estilo para o placeholder na caixa de entrada do chat */
div.stChatInput textarea::placeholder {
    color: white !important;  /* Cor do placeholder branco */
    opacity: 1;  /* Garante que o placeholder seja totalmente visível */
}
   
     /* Estilo para o ícone */
    .stImage > img {
        filter: drop-shadow(0 0 0 #8dc50b);  /* Aplica a cor #8dc50b ao ícone */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Subtítulo com fonte reduzida e texto preto
st.markdown(
    '<cp class="subtitulo">Olá, tudo bem? Sou um chat Co-Piloto. Fui feito para te auxiliar com eventuais demandas e fornecer apoio estratégico em decisões.</p>',
    unsafe_allow_html=True
)

# Inicialização segura das variáveis de estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# Mensagem inicial automática
if not st.session_state.mensagens_chat:
    mensagem_inicial = """Olá, Lukas! 👋  
Como posso te ajudar hoje?

Fique à vontade para perguntar o que quiser."""
    st.session_state.mensagens_chat.append({"user": None, "bot": mensagem_inicial})

# Função para limpar o histórico do chat
def limpar_historico():
    st.session_state.mensagens_chat = []

def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Devolve todo o texto de um PDF localizado em `caminho_pdf`."""
    if not Path(caminho_pdf).exists():
        return ""

    reader = PdfReader(caminho_pdf)
    paginas = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(paginas)

 
CAMINHO_CONTEXTO = "contexto1.txt"


def carregar_contexto() -> str:
    """Lê o arquivo inteiro e devolve como string."""
    if Path(CAMINHO_CONTEXTO).exists():
        return Path(CAMINHO_CONTEXTO).read_text(encoding="utf-8")
    return ""

contexto_inteiro = carregar_contexto()



# Função para dividir o texto em chunks
def dividir_texto(texto, max_tokens=800):  # Chunks menores (800 tokens)
    palavras = texto.split()
    chunks = []
    chunk_atual = ""
    for palavra in palavras:
        if len(chunk_atual.split()) + len(palavra.split()) <= max_tokens:
            chunk_atual += palavra + " "
        else:
            chunks.append(chunk_atual.strip())
            chunk_atual = palavra + " "
    if chunk_atual:
        chunks.append(chunk_atual.strip())
    return chunks

# Função para selecionar chunks relevantes com base na pergunta
def selecionar_chunks_relevantes(pergunta, chunks):
    # Lógica simples para selecionar chunks com base em palavras-chave
    palavras_chave = pergunta.lower().split()
    chunks_relevantes = []
    for chunk in chunks:
        if any(palavra in chunk.lower() for palavra in palavras_chave):
            chunks_relevantes.append(chunk)
    return chunks_relevantes[:2]  # Limita a 2 chunks para evitar excesso de tokens


def limpar_frases_indesejadas(txt: str) -> str:
    for p in _PADROES:
        txt = re.sub(p, "", txt, flags=re.I)
    return txt.strip() or "Informação não disponível no material de apoio."

def gerar_resposta(pergunta: str) -> str:
    client = anthropic.Anthropic(api_key=claude_api_key)

    system_prompt = (
        "Seu nome é CoJudi, você é um chatbot Co-Piloto. "
        "Responda SÓ com base no contexto abaixo. "
        'Dê respostas técnicas e embasadas em conceitos jurídicos'
        "Nunca use as expressões “De acordo com …”.\n\n"
        "—— CONTEXTO ——\n"
        f"{contexto_inteiro}\n"
        "—— FIM DO CONTEXTO ——"
    )

    try:
        resp = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1200,
            temperature=0.1,
            system=system_prompt,
            messages=[{"role": "user", "content": pergunta}]
        )

        resposta_bruta = resp.content[0].text.strip()
        # aplique o filtro se quiser
        resposta_final = limpar_frases_indesejadas(resposta_bruta)

    except Exception as e:
        # mensagem amigável + log opcional
        resposta_final = f"⚠️ Erro ao gerar resposta: {e}"

    return resposta_final

# Interface do Streamlit

if claude_api_key:
    if st.sidebar.button("🧹 Limpar Histórico do Chat", key="limpar_historico"):
        limpar_historico()
        st.sidebar.success("Histórico do chat limpo com sucesso!")


user_input = st.chat_input("💬 Sua pergunta:")
if user_input and user_input.strip():
    st.session_state.mensagens_chat.append({"user": user_input, "bot": None})
    resposta = gerar_resposta(user_input)
    st.session_state.mensagens_chat[-1]["bot"] = resposta

with st.container():
    if st.session_state.mensagens_chat:
        for mensagem in st.session_state.mensagens_chat:
            if mensagem["user"]:
                with st.chat_message("user"):
                    st.markdown(f"**Você:** {mensagem['user']}", unsafe_allow_html=True)
            if mensagem["bot"]:
                with st.chat_message("assistant"):
                    st.markdown(f"**CoJudi:**\n\n{mensagem['bot']}", unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown("*CoJudi:* Nenhuma mensagem ainda.", unsafe_allow_html=True)
