import streamlit as st
import json
import re

st.set_page_config(page_title="DEH-ALMA Course Builder", layout="wide")

# --- SISTEMA DI AUTENTICAZIONE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.warning("🔒 Area Riservata Autori. Inserisci il PIN per accedere.")
        pin_inserito = st.text_input("PIN di accesso", type="password")
        if st.button("Accedi"):
            if pin_inserito == st.secrets["passwords"]["author_pin"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("PIN errato.")
        return False
    return True

if not check_password():
    st.stop()

# --- INIZIALIZZAZIONE DELLO STATO (DATA MODEL) ---
if 'corso' not in st.session_state:
    st.session_state.corso = {
        "titolo": "", "sottotitolo": "", "descrizione_breve": "",
        "descrizione_completa": "", "obiettivi": "",
        "docente_titolo": "", "docente_nome": "", "docente_cognome": "", "cv_autore": "",
        "destinatari": [{"profilo": ""}],
        "argomenti_trattati": []
    }

if 'moduli' not in st.session_state:
    st.session_state.moduli = []

if 'lezioni' not in st.session_state:
    st.session_state.lezioni = []

if 'materiali' not in st.session_state:
    st.session_state.materiali = []

def pulisci_testo_lista(testo_grezzo):
    return [re.sub(r'^[\•\-\*\◦\▪]\s*', '', linea).strip() for linea in str(testo_grezzo).split('\n') if linea.strip()]

def genera_payload():
    """Genera la struttura JSON comune sia per la bozza che per l'export finale"""
    destinatari_validi = [d["profilo"] for d in st.session_state.corso.get("destinatari", []) if isinstance(d, dict) and d.get("profilo", "").strip()]

    corso_export = st.session_state.corso.copy()
    corso_export["destinatari"] = destinatari_validi
    corso_export["argomenti_trattati"] = sorted(st.session_state.corso.get("argomenti_trattati", []), key=lambda x: x.get("ordine", 999))

    moduli_export = sorted(st.session_state.moduli, key=lambda x: x.get("ordine", 999))

    lezioni_ordinate = sorted(st.session_state.lezioni, key=lambda x: x.get("ordine", 999))
    lezioni_export = []
    for lez in lezioni_ordinate:
        lezioni_export.append({
            "ordine": lez.get("ordine", 999),
            "modulo": lez.get("modulo", ""),
            "id": lez.get("id", ""),
            "titolo": lez.get("titolo", ""),
            "youtube_id": lez.get("youtube_id", ""),
            "nome_file_video": lez.get("nome_file_video", ""),
            "argomenti_raw": lez.get("argomenti_raw", ""),
            "argomenti": pulisci_testo_lista(lez.get("argomenti_raw", ""))
        })

    return {
        "metadata_corso": corso_export,
        "struttura_moduli": moduli_export,
        "struttura_lezioni": lezioni_export,
        "risorse_extra": st.session_state.materiali
    }

# ==========================================
# SIDEBAR: GESTIONE PROGETTO
# ==========================================
with st.sidebar:
    st.header("📂 Gestione Progetto")
    st.info("Salva il tuo lavoro in locale se devi interrompere, per poi riprenderlo in seguito.")

    bozza_json = json.dumps(genera_payload(), indent=4, ensure_ascii=False)
    nome_bozza = st.session_state.corso['titolo'].replace(' ', '_').lower() if st.session_state.corso.get('titolo') else "nuovo_corso"
    st.download_button(
        label="💾 Scarica Bozza Incompleta",
        data=bozza_json,
        file_name=f"bozza_{nome_bozza}.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("---")

    uploaded_file = st.file_uploader("📥 Riprendi lavoro da file JSON", type=["json"])
    if uploaded_file is not None:
        if st.button("Carica Dati (Sovrascrive tutto)", use_container_width=True):
            try:
                data = json.load(uploaded_file)
                loaded_corso = data.get("metadata_corso", {})

                dest_raw = loaded_corso.get("destinatari", [])
                loaded_corso["destinatari"] = [{"profilo": d} for d in dest_raw] if dest_raw else [{"profilo": ""}]

                for f in ["docente_titolo", "docente_nome", "docente_cognome"]:
                    if f not in loaded_corso:
                        loaded_corso[f] = ""

                st.session_state.corso.update(loaded_corso)
                st.session_state.moduli = data.get("struttura_moduli", [])
                st.session_state.lezioni = data.get("struttura_lezioni", [])
                st.session_state.materiali = data.get("risorse_extra", [])

                st.success("Progetto caricato!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nel caricamento: {e}")

st.title("🛠️ DEH-ALMA Course Master Builder")
st.markdown("Compila le sezioni per costruire l'architettura del corso. Passa il mouse sopra le icone ❓ per le istruzioni dettagliate.")

tab1, tab2, tab3, tab4 = st.tabs(["📚 1. Info Generali", "🎥 2. Moduli e Lezioni", "📎 3. Materiali Extra", "📦 4. Validazione & Export"])

# ==========================================
# TAB 1: INFO GENERALI
# ==========================================
with tab1:
    st.subheader("Informazioni Master del Corso")

    st.session_state.corso["titolo"] = st.text_input("Titolo del Corso *", st.session_state.corso.get("titolo", ""))
    st.session_state.corso["sottotitolo"] = st.text_input("Sottotitolo *", st.session_state.corso.get("sottotitolo", ""))
    st.session_state.corso["descrizione_breve"] = st.text_area("Descrizione Breve * (1-2 frasi)", st.session_state.corso.get("descrizione_breve", ""))
    st.session_state.corso["descrizione_completa"] = st.text_area("Descrizione Completa *", st.session_state.corso.get("descrizione_completa", ""))
    st.session_state.corso["obiettivi"] = st.text_area("Obiettivi Formativi *", st.session_state.corso.get("obiettivi", ""))

    st.markdown("---")
    st.markdown("### 👨‍🏫 Informazioni Docente / Autore")

    col_t, col_n, col_c = st.columns([1, 2, 2])
    opzioni_titolo = ["", "Prof.", "Prof.ssa", "Dott.", "Dott.ssa"]
    titolo_attuale = st.session_state.corso.get("docente_titolo", "")
    idx_titolo = opzioni_titolo.index(titolo_attuale) if titolo_attuale in opzioni_titolo else 0

    st.session_state.corso["docente_titolo"] = col_t.selectbox("Titolo (Opzionale)", opzioni_titolo, index=idx_titolo)
    st.session_state.corso["docente_nome"] = col_n.text_input("Nome *", st.session_state.corso.get("docente_nome", ""))
    st.session_state.corso["docente_cognome"] = col_c.text_input("Cognome *", st.session_state.corso.get("docente_cognome", ""))
    st.session_state.corso["cv_autore"] = st.text_area("Curriculum Vitae / Bio Docente *", st.session_state.corso.get("cv_autore", ""))

    st.markdown("---")
    st.markdown("### Destinatari del Corso *")
    st.caption("🗑️ **Per eliminare una riga:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' o 'Backspace' sulla tastiera.")

    if not st.session_state.corso.get("destinatari"):
        st.session_state.corso["destinatari"] = [{"profilo": ""}]

    st.session_state.corso["destinatari"] = st.data_editor(
        st.session_state.corso["destinatari"],
        use_container_width=True, num_rows="dynamic", key="edit_destinatari",
        column_config={"profilo": st.column_config.TextColumn("Profilo Destinatario", required=True)}
    )

    st.markdown("---")
    st.markdown("### Argomenti Trattati * (Minimo 1 obbligatorio)")

    with st.form("form_argomenti", clear_on_submit=True):
        col1, col2 = st.columns(2)
        arg_titolo = col1.text_input("Titolo Argomento *")
        arg_desc = col2.text_area("Descrizione Argomento *")
        if st.form_submit_button("➕ Aggiungi Argomento"):
            if not arg_titolo or not arg_desc:
                st.error("Sia il Titolo che la Descrizione dell'argomento sono obbligatori.")
            else:
                nuovo_ordine = len(st.session_state.corso["argomenti_trattati"]) + 1
                st.session_state.corso["argomenti_trattati"].append({"ordine": nuovo_ordine, "titolo": arg_titolo.strip(), "descrizione": arg_desc.strip()})
                st.success("Argomento aggiunto!")

    if st.session_state.corso.get("argomenti_trattati"):
        st.caption("🗑️ **Per eliminare una riga:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' o 'Backspace' sulla tastiera.")
        st.session_state.corso["argomenti_trattati"] = st.data_editor(
            st.session_state.corso["argomenti_trattati"],
            use_container_width=True, num_rows="dynamic", key="edit_argomenti",
            column_config={
                "ordine": st.column_config.NumberColumn("Pos.", min_value=1, step=1, required=True, width="small"),
                "titolo": st.column_config.TextColumn("Titolo Argomento", required=True),
                "descrizione": st.column_config.TextColumn("Descrizione Argomento", required=True)
            }
        )

# ==========================================
# TAB 2: MODULI E VIDEOLEZIONI
# ==========================================
with tab2:
    st.subheader("Gestione Struttura: Moduli e Lezioni")

    if st.session_state.corso.get("argomenti_trattati"):
        if st.button("🔄 Trasforma Argomenti in Moduli"):
            moduli_esistenti = [m["titolo"] for m in st.session_state.moduli]
            aggiunti = 0
            for arg in st.session_state.corso["argomenti_trattati"]:
                if arg["titolo"] not in moduli_esistenti:
                    nuovo_ordine = len(st.session_state.moduli) + 1
                    st.session_state.moduli.append({"ordine": nuovo_ordine, "titolo": arg["titolo"], "descrizione": arg["descrizione"]})
                    aggiunti += 1
            if aggiunti > 0:
                st.success(f"{aggiunti} moduli creati!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 📦 1. Moduli del Corso")

    with st.form("form_modulo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome_modulo = col1.text_input("Nome Modulo *")
        desc_modulo = col2.text_area("Breve introduzione (Opzionale)")
        if st.form_submit_button("Aggiungi Modulo"):
            if not nome_modulo:
                st.error("Il nome del modulo è obbligatorio.")
            else:
                nuovo_ordine = len(st.session_state.moduli) + 1
                st.session_state.moduli.append({"ordine": nuovo_ordine, "titolo": nome_modulo.strip(), "descrizione": desc_modulo.strip()})
                st.success("Modulo creato!")

    if st.session_state.moduli:
        st.caption("🗑️ **Per eliminare un modulo:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' sulla tastiera.")
        st.session_state.moduli = st.data_editor(
            st.session_state.moduli,
            use_container_width=True, num_rows="dynamic", key="edit_moduli",
            column_config={
                "ordine": st.column_config.NumberColumn("Pos.", min_value=1, required=True, width="small"),
                "titolo": st.column_config.TextColumn("Nome Modulo", required=True),
                "descrizione": st.column_config.TextColumn("Descrizione")
            }
        )

    st.markdown("---")
    st.markdown("### 🎥 2. Videolezioni")

    if not st.session_state.moduli:
        st.warning("⚠️ Crea almeno un Modulo per aggiungere delle videolezioni.")
    else:
        moduli_ordinati = sorted(st.session_state.moduli, key=lambda x: x.get("ordine", 999))
        nomi_moduli = [m["titolo"] for m in moduli_ordinati]

        with st.form("form_lezione", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            modulo_selezionato = col1.selectbox("Assegna al Modulo *", nomi_moduli)
            id_lezione = col2.text_input("ID Lezione * (es. 1.1)")
            youtube_id = col3.text_input("ID Video YouTube (Opzionale)")

            col4, col5 = st.columns(2)
            full_title = col4.text_input("Titolo Lezione *")
            nome_file_video = col5.text_input("Nome File Video *", help="Obbligatorio. Nome esatto del file master (es. video_export_v2.mp4).")

            argomenti_raw = st.text_area("Argomenti della lezione (uno per riga) *", help="Inserisci un argomento per riga. Verrà convertito in un elenco puntato.")

            if st.form_submit_button("➕ Aggiungi Lezione"):
                if not id_lezione or not full_title or not nome_file_video or not argomenti_raw:
                    st.error("ID, Titolo, Nome File Video e Argomenti sono campi obbligatori.")
                else:
                    nuovo_ordine = len(st.session_state.lezioni) + 1
                    st.session_state.lezioni.append({
                        "ordine": nuovo_ordine,
                        "modulo": modulo_selezionato,
                        "id": id_lezione.strip(),
                        "titolo": full_title.strip(),
                        "youtube_id": youtube_id.strip(),
                        "nome_file_video": nome_file_video.strip(),
                        "argomenti_raw": argomenti_raw.strip()
                    })
                    st.success("Lezione aggiunta!")

        if st.session_state.lezioni:
            st.caption("🗑️ **Per eliminare una lezione:** Spunta la casella a sinistra e premi 'Canc'. **Per eliminare un singolo argomento:** fai doppio clic sulla cella 'Argomenti' e cancella la riga di testo corrispondente.")
            st.session_state.lezioni = st.data_editor(
                st.session_state.lezioni,
                use_container_width=True, num_rows="dynamic", key="edit_lezioni",
                column_config={
                    "ordine": st.column_config.NumberColumn("Pos.", min_value=1, required=True, width="small"),
                    "modulo": st.column_config.SelectboxColumn("Modulo", options=nomi_moduli, required=True),
                    "id": st.column_config.TextColumn("ID", required=True),
                    "titolo": st.column_config.TextColumn("Titolo", required=True),
                    "youtube_id": st.column_config.TextColumn("ID YouTube"),
                    "nome_file_video": st.column_config.TextColumn("Nome File Video", required=True),
                    "argomenti_raw": st.column_config.TextColumn("Argomenti (Separati da a capo)", required=True)
                }
            )

# ==========================================
# TAB 3: MATERIALI EXTRA
# ==========================================
with tab3:
    st.subheader("Materiali Aggiuntivi (Slide, PDF, Quiz)")

    with st.form("form_materiali", clear_on_submit=True):
        nomi_moduli_mat = [m["titolo"] for m in sorted(st.session_state.moduli, key=lambda x: x.get("ordine", 999))] if st.session_state.moduli else ["Globale"]
        col1, col2 = st.columns(2)
        mod_mat_selezionato = col1.selectbox("Assegna al Modulo (Opzionale)", nomi_moduli_mat)
        tipo_materiale = col2.selectbox("Tipologia", ["Slide", "Dispensa PDF", "Quiz XML", "Task H5P", "Altro"])
        file_selezionato = st.file_uploader("Seleziona file di riferimento")
        desc_materiale = st.text_area("Descrizione o istruzioni")

        if st.form_submit_button("📎 Aggiungi Materiale"):
            nome_file = file_selezionato.name if file_selezionato else "Nessun_file"
            st.session_state.materiali.append({
                "modulo_riferimento": mod_mat_selezionato, "nome_file": nome_file,
                "tipo": tipo_materiale, "descrizione": desc_materiale.strip()
            })
            st.success("Materiale aggiunto!")

    if st.session_state.materiali:
        st.caption("🗑️ **Per eliminare una riga:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' o 'Backspace' sulla tastiera.")
        st.session_state.materiali = st.data_editor(
            st.session_state.materiali,
            use_container_width=True, num_rows="dynamic", key="edit_materiali",
            column_config={
                "modulo_riferimento": st.column_config.SelectboxColumn("Modulo", options=nomi_moduli_mat, required=True),
                "nome_file": st.column_config.TextColumn("Nome File"),
                "tipo": st.column_config.SelectboxColumn("Tipologia", options=["Slide", "Dispensa PDF", "Quiz XML", "Task H5P", "Altro"]),
                "descrizione": st.column_config.TextColumn("Descrizione")
            }
        )

# ==========================================
# TAB 4: ESPORTAZIONE E VALIDAZIONE
# ==========================================
with tab4:
    st.subheader("Riepilogo e Generazione Payload")

    errori_validazione = []

    campi_testo_obbligatori = {
        "titolo": "Titolo del Corso", "sottotitolo": "Sottotitolo",
        "descrizione_breve": "Descrizione Breve", "descrizione_completa": "Descrizione Completa",
        "obiettivi": "Obiettivi Formativi",
        "docente_nome": "Nome Docente", "docente_cognome": "Cognome Docente",
        "cv_autore": "Curriculum Vitae / Bio"
    }
    for chiave, nome_umano in campi_testo_obbligatori.items():
        if not st.session_state.corso.get(chiave, "").strip():
            errori_validazione.append(f"Manca il campo: **{nome_umano}** (Tab 1)")

    destinatari_validi = [d["profilo"] for d in st.session_state.corso.get("destinatari", []) if isinstance(d, dict) and d.get("profilo", "").strip()]
    if not destinatari_validi:
        errori_validazione.append("Devi inserire almeno **1 Destinatario** valido (Tab 1)")

    if len(st.session_state.corso.get("argomenti_trattati", [])) == 0:
        errori_validazione.append("Devi inserire almeno **1 Argomento Trattato** (Tab 1)")

    if len(st.session_state.moduli) == 0:
        errori_validazione.append("Devi creare almeno **1 Modulo** (Tab 2)")

    if len(st.session_state.moduli) > 0:
        moduli_senza_lezioni = [mod["titolo"] for mod in st.session_state.moduli if not any(lez["modulo"] == mod["titolo"] for lez in st.session_state.lezioni)]
        if moduli_senza_lezioni:
            errori_validazione.append(f"Questi moduli non hanno videolezioni: **{', '.join(moduli_senza_lezioni)}** (Tab 2)")

    # Validazione Nome File Video Obbligatorio
    if len(st.session_state.lezioni) > 0:
        lezioni_senza_video = [lez["id"] for lez in st.session_state.lezioni if not lez.get("nome_file_video", "").strip()]
        if lezioni_senza_video:
            errori_validazione.append(f"Le seguenti lezioni non hanno il 'Nome File Video': **{', '.join(lezioni_senza_video)}** (Tab 2)")

    if errori_validazione:
        st.error("❌ **Impossibile esportare il file MASTER.** Risolvi i seguenti errori:")
        for errore in errori_validazione:
            st.markdown(f"- {errore}")
    else:
        st.success("✅ **Validazione Superata!** Il pacchetto è pronto per l'Architect.")

        payload_finale = genera_payload()

        for lez in payload_finale["struttura_lezioni"]:
            lez.pop("argomenti_raw", None)

        json_data = json.dumps(payload_finale, indent=4, ensure_ascii=False)
        nome_export = st.session_state.corso['titolo'].replace(' ', '_').lower()

        st.download_button(
            label="✅ SCARICA MASTER JSON DEL CORSO",
            data=json_data,
            file_name=f"MASTER_{nome_export}.json",
            mime="application/json",
            use_container_width=True
        )