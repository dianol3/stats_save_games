import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh


st.set_page_config(page_title="Gestão de Jogos", layout="wide")

# ======================
# Configurações iniciais
# ======================
JOGOS_DIR = "jogos"
os.makedirs(JOGOS_DIR, exist_ok=True)

st.title("🏟️ Gestão de Jogos")

# ======================
# Criar novo jogo
# ======================
st.subheader("➕ Criar novo jogo")

col1, col2, col3 = st.columns(3)
with col1:
    equipa = st.text_input("Nome da equipa (nossa):")
with col2:
    adversario = st.text_input("Nome do adversário:")
with col3:
    modalidade = st.selectbox("Modalidade:", ["Futebol", "Futsal"])

tempo_parte = st.number_input("Duração da parte (minutos):", min_value=1, value=45)

# Botão para criar novo jogo
# Botão para iniciar novo jogo
if st.button("✅ Iniciar novo jogo"):
    if equipa and adversario:
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{equipa}_vs_{adversario}.json"
        filepath = os.path.join(JOGOS_DIR, filename)
        novo_jogo = {
            "equipa": equipa,
            "adversario": adversario,
            "modalidade": modalidade,
            "tempo_parte": tempo_parte,
            "score": {"nossa": 0, "adversario": 0},
            "part": 1,
            "elapsed_time": 0,
            "faltas_nossa": 0,
            "faltas_adversario": 0,
            "players": [],
            "event_log": [],
            "estado": "em_andamento",
            "data_criacao": datetime.now().isoformat(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(novo_jogo, f)

        # Guarda no session_state
        st.session_state.jogo_selecionado = filename
        st.session_state.ir_para_stats = True  # Flag de redirecionamento
        st.success(f"✅ Novo jogo criado: {equipa} vs {adversario}")

# Redireciona se a flag estiver definida
if st.session_state.get("ir_para_stats", False):
    st.session_state.ir_para_stats = False  # reset
    st.experimental_rerun()  # Força rerun, stats.py será carregado

# ======================
# Lista de jogos
# ======================
st.subheader("📋 Jogos existentes")

# Atualiza a página a cada 2 segundos (2000 ms)
st_autorefresh(interval=2000, key="refresh_jogos")

# Lista apenas ficheiros .json
files = sorted([f for f in os.listdir(JOGOS_DIR) if f.endswith(".json")], reverse=True)

if not files:
    st.info("Ainda não há jogos registados.")
else:
    jogos = []
    for f in files:
        path = os.path.join(JOGOS_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                jogos.append({
                    "Ficheiro": f,
                    "Equipa": data.get("equipa", "—"),
                    "Adversário": data.get("adversario", "—"),
                    "Modalidade": data.get("modalidade", "—"),
                    "Estado": data.get("estado", "—"),
                    "Data": data.get("data_criacao", "—")[:16].replace("T", " ")
                })
        except Exception as e:
            st.error(f"Erro ao ler {f}: {e}")

    for j in jogos:
        col1, col2, col3, col4, col5 = st.columns([3,2,2,1,1])
        col1.markdown(f"**{j['Equipa']} vs {j['Adversário']}**")
        col2.write(f"📅 {j['Data']}")
        col3.write(f"⚙️ {j['Estado']}")
        with col4:
            if st.button("▶️ Continuar", key=f"cont_{j['Ficheiro']}"):
                st.session_state.jogo_selecionado = j["Ficheiro"]
                st.switch_page("stats_app")  # Nome da página multi-page sem .py
        with col5:
            if st.button("🗑️", key=f"del_{j['Ficheiro']}"):
                os.remove(os.path.join(JOGOS_DIR, j["Ficheiro"]))
                # A página vai atualizar automaticamente graças ao st_autorefresh
