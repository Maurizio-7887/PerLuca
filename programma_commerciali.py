import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Funzione per creare la connessione al database SQLite
def create_connection():
    """ Crea una connessione al database SQLite. """
    try:
        conn = sqlite3.connect('sales_data.db')
        return conn
    except sqlite3.Error as e:
        print(e)
        return None

# Funzione per creare la tabella nel database
def create_table(conn):
    """ Crea la tabella 'vendite' nel database, se non esiste già. """
    try:
        sql_create_table = """ CREATE TABLE IF NOT EXISTS vendite (
                                    id integer PRIMARY KEY,
                                    nome_commerciale text NOT NULL,
                                    email_commerciale text NOT NULL,
                                    anno integer NOT NULL,
                                    trimestre integer NOT NULL,
                                    prodotto text NOT NULL,
                                    area_geografica text NOT NULL,
                                    quantita integer NOT NULL,
                                    ricavo real NOT NULL
                                ); """
        c = conn.cursor()
        c.execute(sql_create_table)
    except sqlite3.Error as e:
        print(e)

# Funzione per inserire i dati nel database
def insert_data(conn, data):
    """ Inserisce un record nella tabella 'vendite'. """
    sql = ''' INSERT INTO vendite(nome_commerciale,email_commerciale,anno,trimestre,prodotto,area_geografica,quantita,ricavo)
                  VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()
    return cur.lastrowid

# Funzione per caricare i dati dal database
def load_data(conn):
    """ Carica i dati dalla tabella 'vendite' del database in un DataFrame di Pandas. """
    try:
        sql = 'SELECT nome_commerciale, anno, trimestre, prodotto, area_geografica, quantita, ricavo FROM vendite'
        df = pd.read_sql_query(sql, conn)
        return df
    except sqlite3.Error as e:
        print(e)
        return pd.DataFrame() # Restituisce un DataFrame vuoto in caso di errore

# Funzione per filtrare i dati in base all'email del commerciale
def filter_by_email(conn, email):
    """ Filtra i dati dal database in base all'email del commerciale. """
    try:
        sql = "SELECT nome_commerciale, anno, trimestre, prodotto, area_geografica, quantita, ricavo FROM vendite WHERE email_commerciale = ?"
        df = pd.read_sql_query(sql, conn, params=(email,))
        return df
    except sqlite3.Error as e:
        print(e)
        return pd.DataFrame()

# Funzione per eseguire la query
def query_data(df, anno=None, trimestre=None, prodotto=None, area=None):
    """ Filtra i dati in base ai criteri specificati. """
    query = pd.Series([True] * len(df))  # Inizializza una serie booleana di True

    if anno and anno != "Tutti":
        query = query & (df['anno'] == int(anno))
    if trimestre and trimestre != "Tutti":
        query = query & (df['trimestre'] == int(trimestre))
    if prodotto and prodotto != "Tutti":
        query = query & (df['prodotto'] == prodotto)
    if area and area != "Tutte":
        query = query & (df['area_geografica'] == area)

    return df[query]

# Funzione per ottenere la risposta dell'agente (semplificata)
def get_agent_response(df, domanda):
    """
    Ottiene una risposta alla domanda del commerciale basandosi sui dati filtrati per lui.
    """
    domanda_lower = domanda.lower()

    if df.empty:
        return "Non ci sono dati di vendita disponibili per la tua email."

    if "vendite" in domanda_lower and "anno" in domanda_lower:
        vendite_per_anno = df.groupby('anno')['ricavo'].sum()
        return "Le tue vendite per anno:\n" + "\n".join([f"{anno}: €{ricavo:.2f}" for anno, ricavo in vendite_per_anno.items()])
    elif "vendite" in domanda_lower and "trimestre" in domanda_lower:
        vendite_per_trimestre = df.groupby('trimestre')['ricavo'].sum()
        return "Le tue vendite per trimestre:\n" + "\n".join([f"Trimestre {trim}: €{ricavo:.2f}" for trim, ricavo in vendite_per_trimestre.items()])
    elif "vendite" in domanda_lower and ("prodotto" in domanda_lower or "articolo" in domanda_lower):
        vendite_per_prodotto = df.groupby('prodotto')['ricavo'].sum()
        return "Le tue vendite per prodotto:\n" + "\n".join([f"{prodotto}: €{ricavo:.2f}" for prodotto, ricavo in vendite_per_prodotto.items()])
    elif "vendite" in domanda_lower and ("area" in domanda_lower or "geografica" in domanda_lower or "regione" in domanda_lower):
        vendite_per_area = df.groupby('area_geografica')['ricavo'].sum()
        return "Le tue vendite per area geografica:\n" + "\n".join([f"{area}: €{ricavo:.2f}" for area, ricavo in vendite_per_area.items()])
    elif ("ricavo" in domanda_lower and "totale" in domanda_lower) or "totale ricavo" in domanda_lower:
        ricavo_totale = df['ricavo'].sum()
        return f"Il tuo ricavo totale è di €{ricavo_totale:.2f}."
    elif ("quantità" in domanda_lower and "totale" in domanda_lower) or "totale quantità" in domanda_lower:
        quantita_totale = df['quantita'].sum()
        return f"La tua quantità totale venduta è di {quantita_totale}."
    else:
        return "Non ho capito la domanda. Puoi chiedere informazioni sulle tue vendite per anno, trimestre, prodotto, area, ricavo totale o quantità totale."

def main():
    st.title("Dashboard Interattiva Vendite")

    # Crea la connessione al database
    conn = create_connection()
    if conn is None:
        st.error("Impossibile connettersi al database.")
        return

    # Crea la tabella se non esiste
    create_table(conn)

    # Carica i dati dal CSV e inseriscili nel database
    try:
        df_from_csv = pd.read_csv("sales_data.csv")
        for _, row in df_from_csv.iterrows():
            data = (
                row['Nome Commerciale'],
                row['Email Commerciale'],
                row['Anno'],
                row['Trimestre'],
                row['Prodotto'],
                row['Area Geografica'],
                row['Quantità'],
                row['Ricavo (€)']
            )
            insert_data(conn, data)
        st.success("Dati caricati dal CSV nel database.")
    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati dal CSV: {e}")
        return

    email_commerciale = st.text_input("Inserisci la tua email aziendale:")

    if email_commerciale:
        df_commerciale = filter_by_email(conn, email_commerciale)

        if not df_commerciale.empty:
            st.sidebar.header("Filtri Query")
            anni_disponibili_str = [str(anno) for anno in sorted(df_commerciale['anno'].unique())]
            anno_selezionato = st.sidebar.selectbox("Anno", ["Tutti"] + anni_disponibili_str)
            trimestri_disponibili_str = [str(trimestre) for trimestre in sorted(df_commerciale['trimestre'].unique())]
            trimestre_selezionato = st.sidebar.selectbox("Trimestre", ["Tutti"] + trimestri_disponibili_str)
            prodotti_disponibili = sorted(df_commerciale['prodotto'].unique())
            prodotto_selezionato = st.sidebar.selectbox("Prodotto", ["Tutti"] + list(prodotti_disponibili))
            aree_disponibili = sorted(df_commerciale['area_geografica'].unique())
            area_selezionata = st.sidebar.selectbox("Area Geografica", ["Tutte"] + list(aree_disponibili))

            risultati_query = query_data(
                df_commerciale,
                anno=anno_selezionato if anno_selezionato != "Tutti" else None,
                trimestre=trimestre_selezionato if trimestre_selezionato != "Tutti" else None,
                prodotto=prodotto_selezionato if prodotto_selezionato != "Tutti" else None,
                area=area_selezionata if area_selezionata != "Tutte" else None
            )

            col_main, col_agent = st.columns([2, 1]) # Crea due colonne con proporzioni 2:1

            with col_main:
                st.subheader("Risultati della Query:")
                if not risultati_query.empty:
                    st.dataframe(risultati_query)

                    st.subheader("Statistiche Aggregate:")
                    st.write(f"Ricavo Totale: €{risultati_query['ricavo'].sum():.2f}")
                    st.write(f"Quantità Totale Venduta: {risultati_query['quantita'].sum()}")

                    with st.expander("Mostra statistiche dettagliate"):
                        if st.checkbox("Per Anno"):
                            st.dataframe(risultati_query.groupby('anno').agg({'ricavo': 'sum', 'quantita': 'sum'}))
                        if st.checkbox("Per Trimestre"):
                            st.dataframe(risultati_query.groupby('trimestre').agg({'ricavo': 'sum', 'quantita': 'sum'}))
                        if st.checkbox("Per Prodotto"):
                            st.dataframe(risultati_query.groupby('prodotto').agg({'ricavo': 'sum', 'quantita': 'sum'}))
                        if st.checkbox("Per Area Geografica"):
                            st.dataframe(risultati_query.groupby('area_geografica').agg({'ricavo': 'sum', 'quantita': 'sum'}))
                else:
                    st.info("Nessun risultato trovato con i filtri selezionati.")

            with col_agent:
                st.subheader("Domanda all'Agente:")
                domanda_agente = st.text_input("Poni una domanda sui dati di vendita:")
                if domanda_agente:
                    risposta_agente = get_agent_response(risultati_query, domanda_agente)
                    st.write("Risposta dell'Agente:")
                    st.write(risposta_agente)

        else:
            st.warning("Email non riconosciuta nel database.")

    if conn:
        conn.close()

if __name__ == "__main__":
    main()
