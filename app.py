import streamlit as st
import pandas as pd
import json
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Porra de Calentadas", page_icon="🏆", layout="centered")

# --- 2. BASE DE DATOS LOCAL ---
DATA_FILE = "datos_porra.json"

def cargar_datos():
    if not os.path.exists(DATA_FILE):
        # Datos por defecto la primera vez que se abre
        datos_iniciales = {
            "usuarios": ["Tú", "Amigo 1", "Amigo 2", "Amigo 3", "Amigo 4", "Amigo 5", "Amigo 6", "Amigo 7"],
            "partidos": [
                {"id": 1, "equipo_local": "España", "equipo_visitante": "Brasil", "jugado": False, "res_local": 0, "res_visitante": 0},
                {"id": 2, "equipo_local": "Argentina", "equipo_visitante": "Francia", "jugado": False, "res_local": 0, "res_visitante": 0},
                {"id": 3, "equipo_local": "Inglaterra", "equipo_visitante": "Alemania", "jugado": False, "res_local": 0, "res_visitante": 0}
            ],
            "predicciones": {} 
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(datos_iniciales, f)
        return datos_iniciales
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

datos = cargar_datos()

# --- 3. LÓGICA DE PUNTUACIÓN ---
def calcular_puntuacion(pred_local, pred_visit, res_local, res_visit):
    # Resultado Exacto = 7 Puntos (Pleno)
    if pred_local == res_local and pred_visit == res_visit:
        return 7, True, False 
    
    puntos = 0
    ganador_pred = "Local" if pred_local > pred_visit else "Visitante" if pred_visit > pred_local else "Empate"
    ganador_res = "Local" if res_local > res_visit else "Visitante" if res_visit > res_local else "Empate"
    
    # Acertar Ganador = 3 Puntos
    if ganador_pred == ganador_res:
        puntos += 3
        
    # Acertar Goles Exactos de un equipo = 1 Punto por equipo
    if pred_local == res_local: puntos += 1
    if pred_visit == res_visit: puntos += 1
        
    # Premio Juanchichi: 0 Puntos en total en el partido
    es_juanchichi = True if puntos == 0 else False
    
    return puntos, False, es_juanchichi

# --- 4. INTERFAZ DE LA WEB ---
st.title("🏆 La Porra de Calentadas")

# Menú de navegación
menu = st.sidebar.radio("Menú", ["📝 Hacer Predicciones", "📊 Ranking y Premios", "⚙️ Admin (Resultados Reales)"])

if menu == "📝 Hacer Predicciones":
    st.header("Tus Predicciones")
    
    # Seleccionar quién eres
    usuario_actual = st.selectbox("¿Quién eres? (Elige tu nombre)", datos["usuarios"])
    st.markdown("---")
    
    if usuario_actual not in datos["predicciones"]:
        datos["predicciones"][usuario_actual] = {}
        
    for partido in datos["partidos"]:
        st.subheader(f"⚽ {partido['equipo_local']} vs {partido['equipo_visitante']}")
        
        # Si el partido ya se jugó, mostrar resultados y puntos
        if partido["jugado"]:
            st.info(f"🚩 Partido finalizado. Resultado Real: {partido['res_local']} - {partido['res_visitante']}")
            
            pred = datos["predicciones"][usuario_actual].get(str(partido["id"]))
            if pred:
                st.write(f"Tu predicción fue: {pred['local']} - {pred['visitante']}")
                pts, pleno, juan = calcular_puntuacion(pred['local'], pred['visitante'], partido['res_local'], partido['res_visitante'])
                st.success(f"✨ Aura Points ganados: {pts}")
            else:
                st.warning("No hiciste predicción para este partido.")
        else:
            # Si no se ha jugado, dejar predecir
            col1, col2 = st.columns(2)
            
            pred_previa_local = 0
            pred_previa_visit = 0
            if str(partido["id"]) in datos["predicciones"][usuario_actual]:
                pred_previa_local = datos["predicciones"][usuario_actual][str(partido["id"])]["local"]
                pred_previa_visit = datos["predicciones"][usuario_actual][str(partido["id"])]["visitante"]

            with col1:
                goles_local = st.number_input(f"Goles de {partido['equipo_local']}", min_value=0, step=1, key=f"loc_{partido['id']}", value=pred_previa_local)
            with col2:
                goles_visitante = st.number_input(f"Goles de {partido['equipo_visitante']}", min_value=0, step=1, key=f"vis_{partido['id']}", value=pred_previa_visit)
                
            if st.button(f"Guardar predicción", key=f"btn_{partido['id']}"):
                datos["predicciones"][usuario_actual][str(partido["id"])] = {"local": goles_local, "visitante": goles_visitante}
                guardar_datos(datos)
                st.success("¡Predicción guardada correctamente!")
        st.markdown("---")

elif menu == "📊 Ranking y Premios":
    st.header("🔥 Clasificación de Aura Points")
    
    ranking = []
    for user in datos["usuarios"]:
        puntos_totales = 0
        plenos = 0
        juanchichis = 0
        
        preds_usuario = datos["predicciones"].get(user, {})
        
        for partido in datos["partidos"]:
            if partido["jugado"]:
                pid = str(partido["id"])
                if pid in preds_usuario:
                    pts, pleno, juan = calcular_puntuacion(
                        preds_usuario[pid]["local"], 
                        preds_usuario[pid]["visitante"], 
                        partido["res_local"], 
                        partido["res_visitante"]
                    )
                    puntos_totales += pts
                    if pleno: plenos += 1
                    if juan: juanchichis += 1
                    
        ranking.append({
            "Jugador": user, 
            "Aura Points": puntos_totales, 
            "Plenos": plenos, 
            "Premios Juanchichi": juanchichis
        })
        
    # Crear tabla ordenada
    df_ranking = pd.DataFrame(ranking).sort_values(by="Aura Points", ascending=False).reset_index(drop=True)
    df_ranking.index += 1 # Empezar en 1 en lugar de 0
    st.dataframe(df_ranking, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🏅 Galardones Especiales")
    
    if not df_ranking.empty and df_ranking["Aura Points"].sum() > 0:
        oraculo = df_ranking.sort_values(by="Plenos", ascending=False).iloc[0]
        if oraculo['Plenos'] > 0:
            st.success(f"🥇 **El Oráculo:** {oraculo['Jugador']} con {oraculo['Plenos']} resultados exactos.")
        
        juanchichi = df_ranking.sort_values(by="Premios Juanchichi", ascending=False).iloc[0]
        if juanchichi['Premios Juanchichi'] > 0:
            st.error(f"🤡 **Líder Premio Juanchichi:** {juanchichi['Jugador']} con {juanchichi['Premios Juanchichi']} fallos catastróficos absolutos.")
    else:
        st.write("Aún no hay puntos repartidos.")

elif menu == "⚙️ Admin (Resultados Reales)":
    st.header("Actualizar Resultados Reales")
    st.warning("⚠️ Esta zona es para meter los resultados reales una vez que terminen los partidos del mundial.")
    
    for i, partido in enumerate(datos["partidos"]):
        st.write(f"**{partido['equipo_local']} vs {partido['equipo_visitante']}**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            res_loc = st.number_input(f"Real: {partido['equipo_local']}", min_value=0, step=1, key=f"res_loc_{partido['id']}", value=partido['res_local'])
        with col2:
            res_vis = st.number_input(f"Real: {partido['equipo_visitante']}", min_value=0, step=1, key=f"res_vis_{partido['id']}", value=partido['res_visitante'])
        with col3:
            jugado = st.checkbox("Finalizado", value=partido['jugado'], key=f"jug_{partido['id']}")
            
        if st.button("Guardar Resultado Oficial", key=f"upd_{partido['id']}"):
            datos["partidos"][i]["res_local"] = res_loc
            datos["partidos"][i]["res_visitante"] = res_vis
            datos["partidos"][i]["jugado"] = jugado
            guardar_datos(datos)
            st.success("¡Resultado actualizado en el sistema!")
        st.markdown("---")
