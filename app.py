import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="La Porra de Calentadas", page_icon="🏆", layout="wide")
DATA_FILE = "datos_porra_v3.json"

# --- GENERADOR DE LOS 104 PARTIDOS ---
def generar_partidos_completos():
    partidos = []
    pid = 1
    
    # 1. Fase de Grupos (He metido tus equipos reales del Excel)
    grupos = {
        "A": ["México", "Corea del Sur", "República Checa", "Sudáfrica"],
        "B": ["Canadá", "Bosnia", "Catar", "Suiza"],
        "C": ["Brasil", "Marruecos", "Haití", "Escocia"],
        "D": ["Estados Unidos", "Paraguay", "Australia", "Turquía"],
        "E": ["Alemania", "Curazao", "Costa de Marfil", "Ecuador"],
        "F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
        "G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
        "H": ["España", "Chile", "Arabia Saudita", "Gales"],
        "I": ["Francia", "Bolivia", "Malí", "Ucrania"],
        "J": ["Portugal", "Perú", "Argelia", "Austria"],
        "K": ["Italia", "Colombia", "Uzbekistán", "Dinamarca"],
        "L": ["Inglaterra", "Croacia", "Ghana", "Panamá"]
    }
    
    for letra, equipos in grupos.items():
        cruces = [(0,3), (1,2), (2,0), (3,1), (1,0), (3,2)]
        for i, j in cruces:
            partidos.append({"id": pid, "fase": f"Grupo {letra}", "local": equipos[i], "visitante": equipos[j], "jugado": False, "res_l": 0, "res_v": 0})
            pid += 1

    # 2. Eliminatorias (Plantillas vacías que el Admin rellenará)
    fases_elim = [("16avos de Final", 16), ("Octavos de Final", 8), ("Cuartos de Final", 4), ("Semifinal", 2), ("Tercer Puesto", 1), ("FINAL", 1)]
    
    for nombre_fase, cantidad in fases_elim:
        for _ in range(cantidad):
            partidos.append({"id": pid, "fase": nombre_fase, "local": f"Por Definir (L)", "visitante": f"Por Definir (V)", "jugado": False, "res_l": 0, "res_v": 0})
            pid += 1
            
    return partidos

def cargar_datos():
    if not os.path.exists(DATA_FILE):
        datos_iniciales = {
            "usuarios": [], 
            "partidos": generar_partidos_completos(),
            "predicciones": {} 
        }
        guardar_datos(datos_iniciales)
        return datos_iniciales
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

datos = cargar_datos()

def calcular_puntos(pl, pv, rl, rv):
    if pl == rl and pv == rv: return 7, True, False
    ptos = 0
    g_p = "L" if pl > pv else "V" if pv > pl else "E"
    g_r = "L" if rl > rv else "V" if rv > rl else "E"
    if g_p == g_r: ptos += 3
    if pl == rl: ptos += 1
    if pv == rv: ptos += 1
    return ptos, False, (ptos == 0)

# --- INTERFAZ ---
st.title("🏆 La Porra de Calentadas")
tab_pred, tab_rank, tab_premios, tab_admin = st.tabs(["📝 Apostar", "📊 Ranking", "🏅 Premios Especiales", "⚙️ El Soporte (Admin)"])

# --- APOSTAR ---
with tab_pred:
    if not datos["usuarios"]:
        st.warning("El Soporte debe añadir jugadores en la pestaña de configuración.")
    else:
        user = st.selectbox("👤 ¿Quién eres?", datos["usuarios"])
        if user not in datos["predicciones"]: datos["predicciones"][user] = {}
        
        fase_filtro = st.selectbox("Filtrar por Fase", ["Todas"] + list(dict.fromkeys([p["fase"] for p in datos["partidos"]])))
        
        for p in datos["partidos"]:
            if fase_filtro != "Todas" and p["fase"] != fase_filtro: continue
            
            # Ocultar partidos no definidos para no ensuciar la pantalla
            if "Por Definir" in p["local"]: continue
            
            with st.expander(f"[{p['id']}] {p['fase']}: {p['local']} vs {p['visitante']} {'✅ FINALIZADO' if p['jugado'] else ''}", expanded=not p['jugado']):
                if p["jugado"]:
                    st.info(f"Resultado Real: {p['local']} {p['res_l']} - {p['res_v']} {p['visitante']}")
                    pred = datos["predicciones"][user].get(str(p["id"]))
                    if pred:
                        pts, _, _ = calcular_puntos(pred['l'], pred['v'], p['res_l'], p['res_v'])
                        st.write(f"Tu apuesta: {pred['l']} - {pred['v']} (**+{pts} Aura Points**)")
                else:
                    c1, c2, c3 = st.columns([2,2,1])
                    p_l = datos["predicciones"][user].get(str(p["id"]), {}).get('l', 0)
                    p_v = datos["predicciones"][user].get(str(p["id"]), {}).get('v', 0)
                    
                    with c1: v_l = st.number_input(p['local'], 0, 15, p_l, key=f"pl_{p['id']}")
                    with c2: v_v = st.number_input(p['visitante'], 0, 15, p_v, key=f"pv_{p['id']}")
                    with c3:
                        st.write("")
                        st.write("")
                        if st.button("Guardar", key=f"btn_{p['id']}", use_container_width=True):
                            datos["predicciones"][user][str(p["id"])] = {'l': v_l, 'v': v_v}
                            guardar_datos(datos)
                            st.toast("¡Aura guardado!")

# --- RANKING ---
ranking = []
for u in datos["usuarios"]:
    t_ptos, t_plenos, t_juan = 0, 0, 0
    preds = datos["predicciones"].get(u, {})
    for p in datos["partidos"]:
        if p["jugado"] and str(p["id"]) in preds:
            pts, pleno, juan = calcular_puntos(preds[str(p["id"])]['l'], preds[str(p["id"])]['v'], p['res_l'], p['res_v'])
            t_ptos += pts
            if pleno: t_plenos += 1
            if juan: t_juan += 1
    ranking.append({"Jugador": u, "Aura Points": t_ptos, "Plenos": t_plenos, "Fallos Absolutos": t_juan})

df_rank = pd.DataFrame(ranking)

with tab_rank:
    st.header("🔥 Clasificación General")
    if not df_rank.empty:
        st.dataframe(df_rank[["Jugador", "Aura Points"]].sort_values("Aura Points", ascending=False).reset_index(drop=True), use_container_width=True)

with tab_premios:
    col1, col2 = st.columns(2)
    if not df_rank.empty:
        with col1:
            st.subheader("👁️ El Oráculo")
            st.dataframe(df_rank[["Jugador", "Plenos"]].sort_values("Plenos", ascending=False).reset_index(drop=True), use_container_width=True)
        with col2:
            st.subheader("🤡 Premio Juanchichi")
            st.dataframe(df_rank[["Jugador", "Fallos Absolutos"]].sort_values("Fallos Absolutos", ascending=False).reset_index(drop=True), use_container_width=True)

# --- EL SOPORTE (ADMIN) ---
with tab_admin:
    st.header("Herramientas de Control")
    
    # 1. JUGADORES
    with st.expander("👥 Gestionar Jugadores"):
        nuevo_user = st.text_input("Nombre del nuevo amigo:")
        if st.button("Añadir", key="add_user"):
            if nuevo_user and nuevo_user not in datos["usuarios"]:
                datos["usuarios"].append(nuevo_user)
                guardar_datos(datos)
                st.rerun()

    # 2. DEFINIR CRUCES (ELIMINATORIAS)
    with st.expander("🛠️ Configurar Siguientes Fases (Octavos, Cuartos...)"):
        st.write("Cuando sepas qué equipos pasan de ronda, escríbelos aquí para que la gente pueda apostar.")
        for i, p in enumerate(datos["partidos"]):
            if p["id"] > 72: # Solo partidos de eliminatoria
                c1, c2, c3 = st.columns([1,2,2])
                with c1: st.write(f"**P.{p['id']} - {p['fase']}**")
                with c2: n_l = st.text_input("Local", p['local'], key=f"nl_{p['id']}")
                with c3: n_v = st.text_input("Visitante", p['visitante'], key=f"nv_{p['id']}")
                
                if n_l != p['local'] or n_v != p['visitante']:
                    if st.button("Actualizar Equipos", key=f"upd_eq_{p['id']}"):
                        datos["partidos"][i]["local"] = n_l
                        datos["partidos"][i]["visitante"] = n_v
                        guardar_datos(datos)
                        st.rerun()

    # 3. METER RESULTADOS REALES
    with st.expander("⚽ Validar Resultados (Repartir Puntos)"):
        for i, p in enumerate(datos["partidos"]):
            if "Por Definir" not in p["local"]: # Solo los que ya tienen equipos reales
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1: st.write(f"{p['fase']}: {p['local']} vs {p['visitante']}")
                with c2: r_l = st.number_input("Goles L", 0, 20, p['res_l'], key=f"rrl_{p['id']}")
                with c3: r_v = st.number_input("Goles V", 0, 20, p['res_v'], key=f"rrv_{p['id']}")
                with c4: jug = st.checkbox("Finalizado", p['jugado'], key=f"jj_{p['id']}")
                
                if st.button("Validar Puntos", key=f"val_{p['id']}"):
                    datos["partidos"][i].update({"res_l": r_l, "res_v": r_v, "jugado": jug})
                    guardar_datos(datos)
                    st.rerun()
