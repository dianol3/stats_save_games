import streamlit as st
import pandas as pd
import time
import os
from streamlit_autorefresh import st_autorefresh
import json

# Caminho para os jogos
JOGOS_DIR = "jogos"

# Carregar o jogo selecionado
if "jogo_selecionado" not in st.session_state:
    st.warning("Nenhum jogo selecionado. Volta à página principal.")
    st.stop()
    

jogo_path = os.path.join(JOGOS_DIR, st.session_state.jogo_selecionado)
if not os.path.exists(jogo_path):
    st.error("Ficheiro de jogo não encontrado.")
    st.stop()

# Carregar dados do ficheiro
with open(jogo_path, "r", encoding="utf-8") as f:
    jogo_data = json.load(f)

# Inicializar session_state com dados do jogo
st.session_state.modalidade = jogo_data.get("modalidade", "Futebol")
st.session_state.tempo_parte = jogo_data.get("tempo_parte", 45)
st.session_state.team_name = jogo_data.get("equipa", "")
st.session_state.clube_adversario = jogo_data.get("adversario", "")
st.session_state.score = jogo_data.get("score", {"nossa": 0, "adversario": 0})
st.session_state.part = jogo_data.get("part", 1)
st.session_state.elapsed_time = jogo_data.get("elapsed_time", 0)
st.session_state.faltas_nossa = jogo_data.get("faltas_nossa", 0)
st.session_state.faltas_adversario = jogo_data.get("faltas_adversario", 0)
st.session_state.event_log = jogo_data.get("event_log", [])



st.set_page_config(page_title="Estatísticas Ao Vivo", layout="wide")

# ======================
# Estado da Sessão
# ======================
if 'players' not in st.session_state:
    st.session_state.players = pd.DataFrame()
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'score' not in st.session_state:
    st.session_state.score = {"Nossa":0, "Adversário":0}
if 'part' not in st.session_state:
    st.session_state.part = 1
if 'num_titulares' not in st.session_state:
    st.session_state.num_titulares = 5
if 'game_info_set' not in st.session_state:
    st.session_state.game_info_set = False
if 'modalidade' not in st.session_state:
    st.session_state.modalidade = ''
if 'tempo_parte' not in st.session_state:
    st.session_state.tempo_parte = 45
if 'clube_adversario' not in st.session_state:
    st.session_state.clube_adversario = ''
if 'playing_home' not in st.session_state:
    st.session_state.playing_home = True
if 'team_name' not in st.session_state:
    st.session_state.team_name = ''
if 'faltas_nossa' not in st.session_state:
    st.session_state.faltas_nossa = 0
if 'faltas_adversario' not in st.session_state:
    st.session_state.faltas_adversario = 0
if 'page' not in st.session_state:
    st.session_state.page = 1  # Página 1 = configuração, 2 = titulares, 3 = jogo
if 'event_log' not in st.session_state:
    st.session_state.event_log = []

equipas_path = "Equipas"
team_files = [f for f in os.listdir(equipas_path) if f.endswith('.txt')]

# Mapear ficheiros para nomes
team_names_map = {
    "condeixa.txt": "Condeixa",
    "santaclara.txt": "Santa Clara"
}

# Carregar jogadores
def load_players(team_file):
    filepath = os.path.join(equipas_path, team_file)
    players_list = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) == 2:
                number, name = parts
                players_list.append({
                    'Número': number,
                    'Jogador': name,
                    'Em jogo': False,
                    'Golos':0, 'Assistências':0, 'Perdas de Bola':0, 'Recuperações':0,
                    'Amarelos':0,'Vermelhos':0,'Remates à Baliza':0,'Remates Fora':0,
                    'Faltas Cometidas':0,'Faltas Sofridas':0,'Defesas':0,
                    'Tempo de Jogo':0
                })
    st.session_state.players = pd.DataFrame(players_list)

# ======================
# Funções
# ======================
def remove_last_event(evento, jogador=None):
    """
    Remove a última ocorrência de um evento do log.
    Se 'jogador' for fornecido, só remove eventos daquele jogador.
    Função segura: não gera erro se o log estiver vazio.
    """
    if 'event_log' not in st.session_state or not st.session_state.event_log:
        return  # nada para remover

    # percorre o log de trás para frente
    for i in reversed(range(len(st.session_state.event_log))):
        entry = st.session_state.event_log[i]
        if jogador:
            if evento in entry and jogador in entry:
                st.session_state.event_log.pop(i)
                break
        else:
            if evento in entry:
                st.session_state.event_log.pop(i)
                break

def log_event(descricao, value=1):
    minutos = int(st.session_state.elapsed_time // 60)
    segundos = int(st.session_state.elapsed_time % 60)
    parte = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"
    
    # Se for decremento, remover último log correspondente
    if value < 0:
        for i in reversed(range(len(st.session_state.event_log))):
            if descricao in st.session_state.event_log[i]:
                st.session_state.event_log.pop(i)
                return  # remove apenas o último evento correspondente
    
    # Caso contrário, adicionar normalmente
    st.session_state.event_log.append(f"{parte} {minutos:02d}:{segundos:02d} - {descricao}")

def add_stat(idx, stat, value=1):
    player_name = st.session_state.players.at[idx, 'Jogador']

    if value < 0:
        # Decrementa a estatística
        st.session_state.players.at[idx, stat] = max(0, st.session_state.players.at[idx, stat] + value)

        # Corrige placares/faltas
        if stat == 'Golos':
            st.session_state.score['Nossa'] = max(0, st.session_state.score['Nossa'] + value)
            remove_last_event(f"Golo - {player_name}", player_name)

        elif stat == 'Faltas Cometidas':
            if st.session_state.playing_home:
                st.session_state.faltas_nossa = max(0, st.session_state.faltas_nossa + value)
            else:
                st.session_state.faltas_adversario = max(0, st.session_state.faltas_adversario + value)
            remove_last_event(f"Falta Cometida - {player_name}", player_name)

        elif stat == 'Faltas Sofridas':
            if st.session_state.playing_home:
                st.session_state.faltas_adversario = max(0, st.session_state.faltas_adversario + value)
            else:
                st.session_state.faltas_nossa = max(0, st.session_state.faltas_nossa + value)
            remove_last_event(f"Falta Sofrida - {player_name}", player_name)

        elif stat in ['Amarelos', 'Vermelhos']:
            # Corrige cor da linha automaticamente via style
            st.session_state.players.at[idx, stat] = max(0, st.session_state.players.at[idx, stat])
            remove_last_event(f"{stat} - {player_name}", player_name)

        else:
            # Outros stats
            remove_last_event(f"{stat} - {player_name}", player_name)

        return

    # Incremento
    st.session_state.players.at[idx, stat] += value
    if stat == 'Golos':
        st.session_state.score['Nossa'] += value
        log_event(f"Golo - {player_name}")
        save_game()
    elif stat == 'Faltas Cometidas':
        if st.session_state.playing_home:
            st.session_state.faltas_nossa += value
        else:
            st.session_state.faltas_adversario += value
        log_event(f"Falta Cometida - {player_name}")
        save_game()
    elif stat == 'Faltas Sofridas':
        if st.session_state.playing_home:
            st.session_state.faltas_adversario += value
        else:
            st.session_state.faltas_nossa += value
        log_event(f"Falta Sofrida - {player_name}")
        save_game()
    else:
        log_event(f"{stat} - {player_name}")
        save_game()

def substitute_player(idx_out, idx_in):
    st.session_state.players.at[idx_out, 'Em jogo'] = False
    st.session_state.players.at[idx_in, 'Em jogo'] = True

def update_time():
    if st.session_state.game_started and st.session_state.start_time is not None:
        current_elapsed = time.time() - st.session_state.start_time
        delta = current_elapsed - st.session_state.elapsed_time
        st.session_state.elapsed_time = current_elapsed
        for idx, row in st.session_state.players.iterrows():
            if row['Em jogo']:
                st.session_state.players.at[idx, 'Tempo de Jogo'] += delta / 60

# ======================
# Página 1 - Configuração
# ======================
if st.session_state.page == 1:
    st.title("⚽ Configuração do Jogo")
    modalidade = st.selectbox("Selecione a modalidade:", ["Futebol", "Futsal"])
    equipas_path = "Equipas"
    team_files = [f for f in os.listdir(equipas_path) if f.endswith('.txt')]
    team_name = st.selectbox("Selecione a equipa:", team_files)
    tempo_parte = st.number_input("Duração da parte (minutos):", min_value=1, value=45)
    clube_adversario = st.text_input("Nome do clube adversário")
    playing_home = st.radio("Estamos em casa ou fora?", ["Casa", "Fora"]) == "Casa"

    if st.button("Confirmar Configuração"):
        st.session_state.modalidade = modalidade
        st.session_state.tempo_parte = tempo_parte
        st.session_state.clube_adversario = clube_adversario
        st.session_state.playing_home = playing_home
        st.session_state.team_name = team_name
        load_players(team_name)
        st.session_state.page = 2

# ======================
# Página 2 - Seleção dos Titulares
# ======================
if st.session_state.page == 2:
    st.title("⚽ Seleção dos Titulares")
    num_titulares = st.number_input("Número de titulares:", min_value=1, max_value=11, value=5)
    jogadores_selecionados = []

    if len(st.session_state.players) >= num_titulares:
        for i in range(num_titulares):
            jogador = st.selectbox(
                f"Titular {i+1}:",
                [j for j in st.session_state.players['Jogador'] if j not in jogadores_selecionados],
                key=f'sel_{i}'
            )
            jogadores_selecionados.append(jogador)

        if st.button("Confirmar Titulares"):
            for jogador in jogadores_selecionados:
                idx = st.session_state.players[st.session_state.players['Jogador']==jogador].index[0]
                st.session_state.players.at[idx, 'Em jogo'] = True
                st.session_state.titulares_1a_parte = jogadores_selecionados.copy()
                log_event("Titulares 1ª Parte: " + ", ".join(jogadores_selecionados))
                save_game()
            st.session_state.page = 3  # Página do jogo
    else:
        st.warning("O número de jogadores no ficheiro é menor que o número de titulares definido.")

#----------------------------
# Save game
#----------------------------
def save_game():
    """Guarda o estado atual do jogo no ficheiro JSON"""
    jogo_data = {
        "equipa": st.session_state.team_name,
        "adversario": st.session_state.clube_adversario,
        "modalidade": st.session_state.modalidade,
        "tempo_parte": st.session_state.tempo_parte,
        "score": st.session_state.score,
        "part": st.session_state.part,
        "elapsed_time": st.session_state.elapsed_time,
        "faltas_nossa": st.session_state.faltas_nossa,
        "faltas_adversario": st.session_state.faltas_adversario,
        "event_log": st.session_state.event_log,
        "estado": "em_andamento",
        "data_criacao": jogo_data.get("data_criacao", "agora")
    }
    if "players" in st.session_state and not st.session_state.players.empty:
        jogo_data["players"] = st.session_state.players.to_dict()

    with open(jogo_path, "w", encoding="utf-8") as f:
        json.dump(jogo_data, f, indent=2)

# ======================
# Página 3 - Jogo
# ======================
if st.session_state.page == 3:
    if st.session_state.playing_home:
        st.title(f"{team_names_map.get(st.session_state.team_name, st.session_state.team_name)} vs {st.session_state.clube_adversario}")
    else:
        st.title(f"{st.session_state.clube_adversario} vs {team_names_map.get(st.session_state.team_name, st.session_state.team_name)}")

    # Cronómetro
    update_time()
    if st.session_state.modalidade == "Futebol":
        minutos = int(st.session_state.elapsed_time // 60)
        segundos = int(st.session_state.elapsed_time % 60)
    else:
        tempo_restante = st.session_state.tempo_parte*60 - st.session_state.elapsed_time
        minutos = int(tempo_restante // 60)
        segundos = int(tempo_restante % 60)

    parte_texto = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"
    st.markdown(f"### ⏱️ {parte_texto} - Tempo: {minutos:02d}:{segundos:02d}")

    # Placar e faltas
    if st.session_state.playing_home:
        placar_text = f"{team_names_map.get(st.session_state.team_name)} {st.session_state.score['Nossa']} - {st.session_state.score['Adversário']} {st.session_state.clube_adversario}"
        faltas_text = f"Faltas: {st.session_state.faltas_nossa} / {st.session_state.faltas_adversario}"
    else:
        placar_text = f"{st.session_state.clube_adversario} {st.session_state.score['Adversário']} - {team_names_map.get(st.session_state.team_name)} {st.session_state.score['Nossa']}"
        faltas_text = f"Faltas: {st.session_state.faltas_adversario} / {st.session_state.faltas_nossa}"

    st.markdown(f"### {placar_text}")
    st.markdown(f"#### {faltas_text}")

    # ======================
    # Botão Golo do Adversário
    # ======================
    col_adv1, col_adv2, col_adv3 = st.columns([1,1])
    with col_adv1:
        if st.button("-1 Golo adv", key="golo_adversario_minus"):
            st.session_state.score['Adversário'] -= 1
            if st.session_state.score['Adversário'] < 0:
                st.session_state.score['Adversário'] = 0
            remove_last_event("Golo Adversário")
    with col_adv2:
        if st.button("+1 Golo adv", key="golo_adversario_plus"):
            st.session_state.score['Adversário'] += 1
            log_event("Golo Adversário")
            save_game()
    with col_adv3:
        if st.button("⬅️ Voltar à Gestão de Jogos"):
            save_game()
            st.switch_page("main.py")

    # Botões de controle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Iniciar / Retomar"):
            st.session_state.game_started = True
            if st.session_state.start_time is None:
                st.session_state.start_time = time.time() - st.session_state.elapsed_time
    with col2:
        if st.button("⏸️ Pausar"):
            st.session_state.game_started = False

    # Atualiza automaticamente a cada 1 segundo (1000 ms)
    st_autorefresh(interval=1000, key="refresh")



    # Início 2ª parte / Final do jogo
    if st.session_state.elapsed_time >= st.session_state.tempo_parte*60 and st.session_state.part == 1:
        st.warning("⏸️ Intervalo - 1ª Parte terminada")
        if st.button("Início 2ª Parte"):
            st.session_state.part = 2
            st.session_state.start_time = None
            st.session_state.elapsed_time = 0
            st.session_state.faltas_nossa = 0
            st.session_state.faltas_adversario = 0
            # Guardar titulares da 2ª parte
            titulares_2a_parte = st.session_state.players[st.session_state.players['Em jogo'] == True]['Jogador'].tolist()
            st.session_state.titulares_2a_parte = titulares_2a_parte
            log_event("Titulares 2ª Parte: " + ", ".join(titulares_2a_parte))
            save_game()


    if st.session_state.part == 2 and st.session_state.elapsed_time >= st.session_state.tempo_parte*60:
        if st.button("Final do jogo"):
            st.session_state.game_started = False
            st.success("⚽ Jogo terminado!")

    # ======================
    # Barra lateral de eventos
    # ======================
    st.sidebar.subheader("Selecionar jogador")
    if 'players' in st.session_state and not st.session_state.players.empty and 'Em jogo' in st.session_state.players.columns:
        em_jogo = st.session_state.players[st.session_state.players['Em jogo'] == True]
    else:
        em_jogo = pd.DataFrame()  # vazio, evita erros
    if not em_jogo.empty:
        selected_player = st.sidebar.selectbox("Jogador:", em_jogo['Jogador'])
        idx = st.session_state.players[st.session_state.players['Jogador']==selected_player].index[0]

        st.sidebar.subheader("Eventos")
        eventos = ['Perdas de Bola','Recuperações','Remates à Baliza','Remates Fora','Defesas','Faltas Cometidas','Faltas Sofridas','Golos','Assistências','Amarelos','Vermelhos']
        for ev in eventos:
            col_ev = st.sidebar.columns([2,1,1])
            col_ev[0].markdown(ev)
            if col_ev[2].button("+1", key=f"plus_{ev}"):
                add_stat(idx, ev, 1)
            if col_ev[1].button("-1", key=f"minus_{ev}"):
                add_stat(idx, ev, -1)

    # ======================
    # Substituições
    # ======================
    st.subheader("🔄 Substituições")
    if 'players' in st.session_state and not st.session_state.players.empty and 'Em jogo' in st.session_state.players.columns:
        em_jogo = st.session_state.players[st.session_state.players['Em jogo'] == True]
        banco = st.session_state.players[st.session_state.players['Em jogo'] == False]
    else:
        em_jogo = pd.DataFrame()
        banco = pd.DataFrame()

    if not em_jogo.empty and not banco.empty:
        out_player = st.selectbox("Jogador a sair (Em jogo):", em_jogo['Jogador'], key='out_player')
        in_player = st.selectbox("Jogador a entrar (Banco):", banco['Jogador'], key='in_player')
        if st.button("Confirmar Substituição"):
            idx_out = st.session_state.players[st.session_state.players['Jogador']==out_player].index[0]
            idx_in = st.session_state.players[st.session_state.players['Jogador']==in_player].index[0]
            substitute_player(idx_out, idx_in)
            log_event(f"Substituição - Entra {in_player}, Sai {out_player}")  # regista evento
            save_game()

    # ======================
    # Tabela de jogadores
    # ======================
    def style_player(row):
        if row['Vermelhos'] > 0:
            cor = 'background-color: red'
        elif row['Amarelos'] > 0:
            cor = 'background-color: yellow'
        else:
            cor = ''
        return [cor]*len(row)
    
    st.dataframe(st.session_state.players.style.apply(style_player, axis=1), use_container_width=True)

    # ======================
    # Bloco de Notas - Log do Jogo
    # ======================
    st.subheader("📝 Bloco de Notas do Jogo")
    if 'event_log' in st.session_state and st.session_state.event_log:
        for e in st.session_state.event_log:
            st.markdown(f"- {e}")
    else:
        st.write("Ainda não há eventos registados.")

    # Botão para download do log
    log_text = "\n".join(st.session_state.event_log)
    st.download_button(
        label="📥 Download Bloco de Notas",
        data=log_text,
        file_name="bloco_de_notas_jogo.txt",
        mime="text/plain"
    )












