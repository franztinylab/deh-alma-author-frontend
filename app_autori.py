import streamlit as st
import streamlit.components.v1 as components
import json
import re
import hashlib

st.set_page_config(page_title="DEH-ALMA Course Builder", layout="wide")

st.markdown("""
    <style>
    /* Forza la rimozione delle istruzioni di input in inglese dai form */
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

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

# Iniezione JavaScript per prevenire la chiusura accidentale della finestra del browser
components.html("""
    <script>
        const parentWindow = window.parent || window;
        parentWindow.addEventListener("beforeunload", function (e) {
            // Mostra il prompt nativo del browser "Vuoi davvero uscire?"
            e.preventDefault();
            e.returnValue = 'Hai delle modifiche non salvate. Sei sicuro di voler uscire?';
        });
    </script>
""", height=0, width=0)

def get_current_hash():
    """Calcola l'impronta digitale esatta dello stato corrente del progetto"""
    payload = genera_payload()
    # Usiamo sort_keys=True per garantire che l'ordine delle chiavi non alteri l'hash
    payload_string = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload_string.encode('utf-8')).hexdigest()

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
if 'intro_video' not in st.session_state:
    st.session_state.intro_video = {"nome_file_video": ""}

if 'last_saved_hash' not in st.session_state:
    st.session_state['last_saved_hash'] = get_current_hash()

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
            "nome_file_video": lez.get("nome_file_video", ""),
            "argomenti_raw": lez.get("argomenti_raw", ""),
            "argomenti": pulisci_testo_lista(lez.get("argomenti_raw", ""))
        })

    lezione_intro = {
        "ordine": 0,
        "modulo": "Presentazione del corso",
        "id": "0.1",
        "titolo": "Introduzione al corso",
        "nome_file_video": st.session_state.intro_video.get("nome_file_video", ""),
        "argomenti": ["Introduzione e presentazione del corso"]
    }

    lezioni_export.insert(0, lezione_intro) # Inserisce la lezione 0.1 in cima a tutte

    return {
        "metadata_corso": corso_export,
        "intro_video": st.session_state.intro_video, # Salvato per permettere il ricaricamento del JSON
        "struttura_moduli": moduli_export,
        "struttura_lezioni": lezioni_export,
        "risorse_extra": st.session_state.materiali
    }

# ==========================================
# SIDEBAR: GESTIONE PROGETTO
# ==========================================
with st.sidebar:
    st.header("📂 Gestione Progetto")

    # MODALE POPUP CONTESTUALE PER LA SIDEBAR
    with st.popover("❓ Come funziona il salvataggio?"):
        st.info("""
        **⚠️ Nessun dato viene salvato online.**
        Questa applicazione vive solo nella memoria temporanea del tuo browser.
        Se ricarichi la pagina (F5) o chiudi la finestra, **perderai tutto**.

        **Per non perdere il lavoro:**
        1. Clicca su **Scarica Bozza parziale**.
        2. Verrà scaricato un file `bozza_...json` sul tuo computer.
        3. Quando vorrai riprendere il lavoro, trascina quel file nel riquadro sottostante e clicca **Carica Dati**.
        """)

    # --- CALCOLO STATO SALVATAGGIO ---
    current_hash = get_current_hash()
    is_dirty = current_hash != st.session_state["last_saved_hash"]

    if is_dirty:
        st.warning("⚠️ Hai delle modifiche non salvate. Ricordati di scaricare la bozza!")
    else:
        st.success("✅ Tutte le modifiche sono state salvate.")

    def imposta_come_salvato():
        """Callback eseguita quando l'utente preme il tasto Scarica"""
        st.session_state["last_saved_hash"] = get_current_hash()

    bozza_json = json.dumps(genera_payload(), indent=4, ensure_ascii=False)
    nome_bozza = st.session_state.corso['titolo'].replace(' ', '_').lower() if st.session_state.corso.get('titolo') else "nuovo_corso"

    st.download_button(
        label="💾 Scarica Bozza parziale",
        data=bozza_json,
        file_name=f"bozza_{nome_bozza}.json",
        mime="application/json",
        use_container_width=True,
        on_click=imposta_come_salvato
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
                lezioni_caricate = data.get("struttura_lezioni", [])
                st.session_state.lezioni = [lez for lez in lezioni_caricate if lez.get("id") != "0.1" and lez.get("titolo") != "Introduzione al corso"]
                st.session_state.materiali = data.get("risorse_extra", [])
                st.session_state.intro_video = data.get("intro_video", {"nome_file_video": ""})

                # Aggiorna l'hash per far diventare il semaforo Verde!
                st.session_state["last_saved_hash"] = get_current_hash()

                st.success("Progetto caricato!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nel caricamento: {e}")

st.title("🛠️ DEH-ALMA Dati del corso")

# AGGIUNTA DELLA QUINTA TAB PER LA GUIDA
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 1. Info Generali",
    "🎥 2. Moduli e Lezioni",
    "📎 3. Materiali Extra",
    "📦 4. Validazione & Export",
    "❓ 5. Guida e Supporto"
])

# ==========================================
# TAB 1: INFO GENERALI
# ==========================================
with tab1:
    col_tit, col_help = st.columns([8, 2])
    with col_tit:
        st.subheader("Informazioni base del corso")
    with col_help:
        with st.popover("ℹ️ Aiuto Info Generali"):
            st.info("""
                    Questi dati appariranno nella **pagina di presentazione del corso**. I campi con l'asterisco (*) sono obbligatori per completare le informazioni.
                    * **Titolo del Corso**: Il nome ufficiale del corso.
                    * **Sottotitolo**: Una breve descrizione che accompagna il titolo.
                    * **Descrizione Breve**: Una sintesi del corso, visibile nella pagina di copertina.
                    * **Descrizione Completa**: Una descrizione dettagliata del corso, visibile nel Syllabus.
                    * **Obiettivi Formativi**: Le competenze che gli studenti acquisiranno.
                    """)

    st.session_state.corso["titolo"] = st.text_input("Titolo del Corso *", st.session_state.corso.get("titolo", ""))
    st.session_state.corso["sottotitolo"] = st.text_input("Sottotitolo *", st.session_state.corso.get("sottotitolo", ""))
    st.session_state.corso["descrizione_breve"] = st.text_area("Descrizione Breve * (1-2 frasi)", st.session_state.corso.get("descrizione_breve", ""))
    st.session_state.corso["descrizione_completa"] = st.text_area("Descrizione Completa * (1-2 paragrafi)", st.session_state.corso.get("descrizione_completa", ""))
    st.session_state.corso["obiettivi"] = st.text_area("Obiettivi Formativi * (3-4 punti elenco)", st.session_state.corso.get("obiettivi", ""))

    st.markdown("---")
    col_doc, col_doc_help = st.columns([8, 2])
    with col_doc:
        st.markdown("### 👨‍🏫 Informazioni Docente / Autore")
    with col_doc_help:
        with st.popover("ℹ️ Aiuto Bio Docente"):
            st.info("""
            **Linee guida per il Curriculum:**
            Le informazioni devono essere **brevi ed essenziali** perché compariranno nella pagina di presentazione del corso sotto la foto o le iniziali del docente.
            Inserisci esclusivamente:
            * **Titoli accademici** rilevanti.
            * **Certificazioni** principali se possedute.
            * **Competenze specifiche** in relazione agli argomenti di questo corso.
            """)

    col_t, col_n, col_c = st.columns([1, 2, 2])
    opzioni_titolo = ["", "Prof.", "Prof.ssa", "Dott.", "Dott.ssa"]
    titolo_attuale = st.session_state.corso.get("docente_titolo", "")
    idx_titolo = opzioni_titolo.index(titolo_attuale) if titolo_attuale in opzioni_titolo else 0

    st.session_state.corso["docente_titolo"] = col_t.selectbox("Titolo (Opzionale)", opzioni_titolo, index=idx_titolo)
    st.session_state.corso["docente_nome"] = col_n.text_input("Nome *", st.session_state.corso.get("docente_nome", ""))
    st.session_state.corso["docente_cognome"] = col_c.text_input("Cognome *", st.session_state.corso.get("docente_cognome", ""))

    st.session_state.corso["cv_autore"] = st.text_area("Curriculum Vitae / Bio Docente *", st.session_state.corso.get("cv_autore", ""))

    st.markdown("---")

    col_dest, col_dest_help = st.columns([8, 2])
    with col_dest:
        st.markdown("### 👥 Destinatari del Corso *")
    with col_dest_help:
        with st.popover("ℹ️ Aiuto Destinatari"):
            st.info("Compila il campo sottostante e clicca su **➕ Aggiungi Destinatario** per ogni profilo a cui è rivolto il corso (es. Studenti di... , Liberi Professionisti, Personale Amministrativo).")

    if "destinatari" not in st.session_state.corso or not st.session_state.corso["destinatari"]:
        st.session_state.corso["destinatari"] = []

    with st.form("form_destinatari", clear_on_submit=True):
        nuovo_profilo = st.text_input("Inserisci Profilo Destinatario (es. Studenti di Informatica, Personale Amministrativo, ecc.)")
        if st.form_submit_button("➕ Aggiungi Destinatario"):
            if not nuovo_profilo.strip():
                st.error("Il campo profilo non può essere vuoto.")
            else:
                st.session_state.corso["destinatari"] = [d for d in st.session_state.corso["destinatari"] if d.get("profilo", "").strip() != ""]
                st.session_state.corso["destinatari"].append({"profilo": nuovo_profilo.strip()})
                st.success("Destinatario aggiunto!")
                st.rerun()

    destinatari_validi = [d for d in st.session_state.corso.get("destinatari", []) if d.get("profilo", "").strip() != ""]
    if destinatari_validi:
        st.caption("🗑️ **Per eliminare una riga:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' o 'Backspace' sulla tastiera.")
        st.session_state.corso["destinatari"] = st.data_editor(
            st.session_state.corso["destinatari"],
            use_container_width=True, num_rows="dynamic", key="edit_destinatari",
            column_config={"profilo": st.column_config.TextColumn("Profilo Destinatario", required=True)}
        )

    st.markdown("---")
    col_arg, col_arg_help = st.columns([8, 2])
    with col_arg:
        st.markdown("### 📋 Argomenti Trattati * (Minimo 1)")
    with col_arg_help:
        with st.popover("ℹ️ Aiuto Argomenti"):
            st.info("""
            **Linee guida per gli Argomenti:**
            Questi rappresentano i **macro-temi** o le unità didattiche principali che compongono il tuo corso. Ogni argomento diventerà una sezione del corso nella piattaforma online.
            * **Titolo Argomento**: Un titolo chiaro e conciso (es. 'Basi di Anatomia').
            * **Descrizione**: Un breve riassunto dei concetti chiave che verranno affrontati in questo blocco.
            * 💡 *Suggerimento:* Puoi far coincidere gli argomenti trattati con i moduli didattici nei quali sono suddivise le videolezioni. Nella Tab successiva troverai un pulsante per trasformare automaticamente questi argomenti nei **Moduli didattici** senza doverli riscrivere.
            """)

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
    col_mod, col_mod_help = st.columns([8, 2])
    with col_mod:
        st.subheader("Gestione Struttura del corso: Moduli didattici e Lezioni")
    with col_mod_help:
        with st.popover("ℹ️ Aiuto Struttura"):
            st.info("""
            **Per strutturare il corso:**
            * Crea i **Moduli didattici** assegnando un nome chiaro e conciso e una descrizione dei contenuti.
            * Ogni Modulo rappresenta un blocco tematico del corso e conterrà una o più Videolezioni.
            * Ogni modulo ha un ordine che determina la sequenza di visualizzazione nel corso. Puoi modificare l'ordine dei moduli modificando il numero nella colonna 'Pos.'.
            * Aggiungi le **Videolezioni** assegnandole a un Modulo didattico specifico tramite il menu a tendina.
            * Ogni Videolezione deve avere un titolo, un nome file video e una lista di argomenti trattati (uno per riga).
            * Ogni modulo deve contenere almeno una videolezione per garantire una struttura coerente del corso.
            """)

    if st.session_state.corso.get("argomenti_trattati"):
        st.markdown("#### ⚡ Automazione Struttura")
        col_btn, col_btn_help = st.columns([8, 2])

        with col_btn:
            esegui_trasformazione = st.button("🔄 Trasforma Argomenti in Moduli", use_container_width=True)

        with col_btn_help:
            with st.popover("ℹ️ Cos'è questo?"):
                st.info("""
                **Automazione Workflow:**
                Cliccando questo pulsante, il sistema leggerà gli **Argomenti Trattati** inseriti nella *Tab 1* e genererà automaticamente i **Moduli didattici** corrispondenti in questa scheda.

                *Note tecniche:*
                - Utile per creare rapidamente la struttura del corso.
                - Il sistema controlla i duplicati: se hai già creato un modulo didattico con lo stesso nome, non verrà sovrascritto o sdoppiato.
                """)

        if esegui_trasformazione:
            moduli_esistenti = [m["titolo"] for m in st.session_state.moduli]
            aggiunti = 0

            for arg in st.session_state.corso["argomenti_trattati"]:
                if arg["titolo"] not in moduli_esistenti:
                    nuovo_ordine = len(st.session_state.moduli) + 1
                    st.session_state.moduli.append({
                        "ordine": nuovo_ordine,
                        "titolo": arg["titolo"],
                        "descrizione": arg.get("descrizione", "")
                    })
                    aggiunti += 1

            if aggiunti > 0:
                st.success(f"✅ Pipeline eseguita: {aggiunti} moduli generati dagli argomenti!")
                st.rerun()
            else:
                st.info("Sincronizzazione completata: Tutti gli argomenti sono già presenti come moduli.")

    st.markdown("---")
    st.markdown("### 📦 1. Moduli del Corso")

    with st.form("form_modulo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome_modulo = col1.text_input("Nome Modulo *")
        desc_modulo = col2.text_area("Breve descrizione (Opzionale)")
        if st.form_submit_button("➕ Aggiungi Modulo"):
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
    st.markdown("### 🎬 2.0 Videolezione Introduttiva (breve introduzione di circa 2 minuti)")
    st.info("Questa lezione ha ID **0.1** e titolo '**Introduzione al corso**' preimpostati dal sistema. Inserisci solo il nome del file video.")

    st.session_state.intro_video["nome_file_video"] = st.text_input("Nome File Video (Intro) *", st.session_state.intro_video.get("nome_file_video", ""))


    st.markdown("---")
    col_lez, col_lez_help = st.columns([8, 2])
    with col_lez:
        st.markdown("### 🎥 2.1 Videolezioni")
    with col_lez_help:
        with st.popover("ℹ️ Aiuto Videolezioni"):
            st.info("""
            **Linee guida per le Videolezioni:**
            Ogni lezione deve fare parte di uno dei Moduli didattici creati in precedenza.
            * **Titolo Lezione:** Il nome visibile agli studenti per questa specifica pillola video.
            * **Nome File Video:** Inserisci il nome **esatto** del file video (es. `modulo1_lezione1.mp4`).
            * **Argomenti della lezione:** Manda a capo ogni singolo concetto. Il sistema trasformerà automaticamente il tuo testo in un elenco puntato sotto al video sulla piattaforma.
            """)

    if not st.session_state.moduli:
        st.warning("⚠️ Crea almeno un Modulo per aggiungere delle videolezioni.")
    else:
        moduli_ordinati = sorted(st.session_state.moduli, key=lambda x: x.get("ordine", 999))
        nomi_moduli = [m["titolo"] for m in moduli_ordinati]

        with st.form("form_lezione", clear_on_submit=True):
            modulo_selezionato = st.selectbox("Assegna al Modulo *", nomi_moduli)

            col1, col2 = st.columns(2)
            full_title = col1.text_input("Titolo Lezione *")
            nome_file_video = col2.text_input("Nome File Video *")

            argomenti_raw = st.text_area("Argomenti della lezione (uno per riga) *")

            if st.form_submit_button("➕ Aggiungi Lezione"):
                if not full_title or not nome_file_video or not argomenti_raw:
                    st.error("Titolo, Nome File Video e Argomenti sono campi obbligatori.")
                else:
                    nuovo_ordine = len(st.session_state.lezioni) + 1
                    st.session_state.lezioni.append({
                        "ordine": nuovo_ordine,
                        "modulo": modulo_selezionato,
                        "id": "",
                        "titolo": full_title.strip(),
                        "nome_file_video": nome_file_video.strip(),
                        "argomenti_raw": argomenti_raw.strip()
                    })
                    st.success("Lezione aggiunta!")
                    st.rerun()

        if st.session_state.lezioni:
            moduli_ordini = {m["titolo"]: m["ordine"] for m in moduli_ordinati}
            contatori_lezioni = {m["titolo"]: 1 for m in moduli_ordinati}

            # 1. Ordina in base all'ordine del modulo e poi all'ordine della lezione digitato dall'utente
            lezioni_ordinate = sorted(st.session_state.lezioni, key=lambda x: (moduli_ordini.get(x["modulo"], 999), x.get("ordine", 999)))

            # 2. Riassegna in automatico ID e Posizione normalizzata (1, 2, 3...) per ogni modulo
            for lez in lezioni_ordinate:
                nome_mod = lez["modulo"]
                ordine_mod = moduli_ordini.get(nome_mod, 999)
                prog_lez = contatori_lezioni.get(nome_mod, 1)

                lez["id"] = f"{ordine_mod}.{prog_lez}" # Ricalcola l'ID (es. 1.1)
                lez["ordine"] = prog_lez              # Ricalcola la posizione visiva

                contatori_lezioni[nome_mod] = prog_lez + 1

            st.session_state.lezioni = lezioni_ordinate

            st.caption("💡 **Per spostare una lezione:** Cambia il suo **Modulo** o il numero **Pos.**. L'ID si aggiornerà da solo.\n🗑️ **Per eliminare:** Spunta la casella a sinistra e premi 'Canc'.")

            # WRAP DEL DATA_EDITOR IN UN FORM PER BLOCCARE L'AUTO-REFRESH
            with st.form("form_aggiorna_lezioni"):
                lezioni_modificate = st.data_editor(
                    st.session_state.lezioni,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="edit_lezioni",
                    column_config={
                        "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                        "ordine": st.column_config.NumberColumn("Pos.", min_value=1, step=1, required=True, width="small"),
                        "modulo": st.column_config.SelectboxColumn("Modulo", options=nomi_moduli, required=True),
                        "titolo": st.column_config.TextColumn("Titolo", required=True),
                        "nome_file_video": st.column_config.TextColumn("Nome File Video", required=True),
                        "argomenti_raw": st.column_config.TextColumn("Argomenti testuali", required=True),
                        "argomenti": None,
                    }
                )

                # IL PULSANTE DI AGGIORNAMENTO MANUALE
                if st.form_submit_button("💾 Salva Modifiche Tabella Lezioni"):
                    st.session_state.lezioni = lezioni_modificate
                    st.success("Modifiche alle lezioni salvate con successo!")
                    st.rerun()

# ==========================================
# TAB 3: MATERIALI EXTRA
# ==========================================
with tab3:
    col_mat, col_mat_help = st.columns([8, 2])
    with col_mat:
        st.subheader("Materiali Aggiuntivi (Slide, PDF, Quiz)")
    with col_mat_help:
        with st.popover("ℹ️ Aiuto Materiali"):
            st.info("""
            **Inserimento Nome File:**
            * Seleziona a quale Modulo didattico assegnare il materiale.
            * Digita il nome esatto del file comprensivo di estensione (es. `slide_modulo1.pdf` oppure `quiz_finale.docx`).
            * Assicurati che questo nome corrisponda **esattamente** al file fisico che consegnerai al Moodle Architect per evitare errori di link interrotti sulla piattaforma.
            """)

    moduli_creati = [m["titolo"] for m in sorted(st.session_state.moduli, key=lambda x: x.get("ordine", 999))]
    nomi_moduli_mat = ["Tutti"] + moduli_creati

    with st.form("form_materiali", clear_on_submit=True):
        col1, col2 = st.columns(2)
        mod_mat_selezionato = col1.selectbox("Assegna al Modulo *", nomi_moduli_mat)
        tipo_materiale = col2.selectbox("Tipologia", ["Slide", "Dispensa", "Quiz", "Trascrizione", "Bibliografia", "Altro"])
        nome_file_input = st.text_input("Nome File *")
        desc_materiale = st.text_area("Descrizione o istruzioni")

        if st.form_submit_button("➕ Aggiungi Materiale"):
            if not nome_file_input.strip():
                st.error("Il Nome File è obbligatorio.")
            else:
                st.session_state.materiali.append({
                    "modulo_riferimento": mod_mat_selezionato,
                    "nome_file": nome_file_input.strip(),
                    "tipo": tipo_materiale,
                    "descrizione": desc_materiale.strip()
                })
                st.success("Materiale aggiunto!")
                st.rerun()

    if st.session_state.materiali:
        st.caption("🗑️ **Per eliminare una riga:** Spunta la casella alla sua sinistra e premi il tasto 'Canc' o 'Backspace' sulla tastiera.")
        st.session_state.materiali = st.data_editor(
            st.session_state.materiali,
            use_container_width=True, num_rows="dynamic", key="edit_materiali",
            column_config={
                "modulo_riferimento": st.column_config.SelectboxColumn("Modulo", options=nomi_moduli_mat, required=True),
                "nome_file": st.column_config.TextColumn("Nome File", required=True),
                "tipo": st.column_config.SelectboxColumn("Tipologia", options=["Slide", "Dispensa", "Quiz", "Trascrizione", "Bibliografia", "Altro"]),
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

    if not st.session_state.intro_video.get("nome_file_video", "").strip():
        errori_validazione.append("Manca il **Nome File Video** per la Lezione Introduttiva 0.1 (Tab 2)")

    if len(st.session_state.moduli) > 0:
        moduli_senza_lezioni = [mod["titolo"] for mod in st.session_state.moduli if not any(lez["modulo"] == mod["titolo"] for lez in st.session_state.lezioni)]
        if moduli_senza_lezioni:
            errori_validazione.append(f"Questi moduli non hanno videolezioni: **{', '.join(moduli_senza_lezioni)}** (Tab 2)")

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
            label="✅ SCARICA FILE MASTER JSON DEL CORSO",
            data=json_data,
            file_name=f"MASTER_{nome_export}.json",
            mime="application/json",
            use_container_width=True
        )

# ==========================================
# TAB 5: GUIDA E SUPPORTO (DOCUMENTATION LAYER)
# ==========================================
with tab5:
    st.header("📖 Manuale d'Uso: DEH-ALMA Course Builder")

    st.markdown("""
    ### 🎯 1. Finalità dell'Applicazione
    Questo strumento sostituisce la compilazione manuale di file di testo o Word. Permette a te (Autore) di concentrarti esclusivamente sui **contenuti didattici**, garantendo al contempo che i dati vengano consegnati al team tecnico in un formato strutturato e privo di errori.
    L'Architect utilizzerà il file JSON che genererai qui per **automatizzare la creazione della piattaforma Moodle** e il processamento video.

    ---

    ### 💾 2. Come Funziona il Salvataggio e Ripristino (MOLTO IMPORTANTE)
    **Attenzione: Questa applicazione non è collegata a un database online.** Tutti i dati che scrivi vivono unicamente nella memoria provvisoria del tuo browser. Se ricarichi la pagina, chiudi la scheda o spegni il PC, **i dati andranno persi**.

    Per prevenire la perdita dei dati o lavorare in più sessioni:
    1. Guarda la **Barra Laterale a sinistra** (Gestione Progetto).
    2. Clicca sul pulsante **"💾 Scarica Bozza parziale"**. Questo salverà sul tuo computer un file di salvataggio (anche se il corso è incompleto e presenta errori).
    3. Quando sei pronto a riprendere il lavoro, riapri questa pagina web.
    4. Trascina il file `bozza_...json` scaricato in precedenza nell'area **"📥 Riprendi lavoro da file JSON"** nella barra laterale.
    5. Clicca su **"Carica Dati"**. L'interfaccia si popolerà istantaneamente con il tuo lavoro precedente.

    ---

    ### ⚡ 3. Automazione Struttura: Dagli Argomenti ai Moduli
    Per massimizzare l'efficienza e garantire la coerenza didattica, la piattaforma include una funzione di sincronizzazione automatica.
    * Nella **Tab 2 (Moduli e Lezioni)** troverai il pulsante **"🔄 Trasforma Argomenti in Moduli"**.
    * Cliccandolo, il sistema leggerà tutti gli *Argomenti Trattati* che hai inserito nella Tab 1 e creerà automaticamente le "scatole" dei moduli corrispondenti.
    * **Prevenzione Errori:** Il sistema è intelligente. Se hai già creato alcuni moduli manualmente, aggiungerà solo gli argomenti mancanti, senza creare duplicati o cancellare il tuo lavoro.

    ---

    ### ✏️ 4. Come Modificare o Eliminare i Dati Inseriti
    Ogni volta che aggiungi un dato tramite i pulsanti "+ Aggiungi", questo appare in una tabella sottostante. **Queste tabelle sono interattive come un foglio Excel:**
    * **Per Modificare:** Fai semplicemente *doppio clic* sulla cella che vuoi correggere e digita il nuovo testo. Premi Invio per confermare.
    * **Per Eliminare:** Metti la spunta sulla casella (checkbox) posta all'estrema sinistra della riga che vuoi eliminare. Poi premi il tasto **Canc** (o Backspace) sulla tua tastiera.
    * **Per Riordinare:** Molte tabelle possiedono la colonna **"Pos."** (Posizione). Fai doppio clic sul numero e modificalo per cambiare l'ordine di presentazione dei moduli, degli argomenti o delle lezioni.

    ---

    ### ✅ 5. Esportazione Finale (Tab 4)
    Quando hai finito di inserire l'intero corso, vai alla **Tab 4 (Validazione & Export)**.
    Il sistema farà un controllo di qualità (Gatekeeper) per assicurarsi che:
    * Siano stati compilati tutti i campi testuali di base (Titolo, Docente, ecc.).
    * Ci sia almeno un Argomento, un Destinatario e un Modulo.
    * **Ogni modulo abbia almeno una videolezione al suo interno.**
    * **Ogni videolezione abbia il nome del file video associato.**

    Finché questi requisiti non sono soddisfatti, vedrai una lista di avvisi in rosso e il pulsante finale sarà bloccato. Una volta risolti, apparirà il bottone verde **"✅ SCARICA MASTER JSON DEL CORSO"**. Invia questo file al tuo Moodle Architect per avviare il deployment automatico.
    """)