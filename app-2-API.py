#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 23:25:25 2025

@author: francescocalzati
"""

import streamlit as st
import pandas as pd
import json

from datetime import datetime
import os

# Add this right after your imports, replacing any other CSS
st.markdown("""
<style>
/* Mobile debugging */
@media (max-width: 768px) {
    .stContainer, .element-container {
        overflow: visible !important;
        width: 100% !important;
    }
    
    /* Force all form elements to be visible */
    .stSelectbox, .stRadio, .stText {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
}
</style>
""", unsafe_allow_html=True)
# ======================
# GOOGLE SHEETS SETTINGS
# ======================

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Inserisci qui gli ID dei fogli (copiati dall’URL tra /d/ e /edit)
MAIN_SPREADSHEET_ID = "1cm7OHOWZS85RnAv5W9_Vz5KTxFfVh3DCFKk8elMrF_I"       # <-- ID foglio RESUMO
DETAIL_SPREADSHEET_ID = "1FzILKPyrpWLG6j17BrAjalu9ds76WNyaXzaGsQooQOc"    # <-- ID foglio DETALHES

# Ordine delle colonne (deve corrispondere alle intestazioni nei Google Sheets)
MAIN_COLUMNS = [
    "timestamp",
    "company_id",
    "num_trabalhadores",
    "tipo_organizacao",
    "regiao",
    "num_pps_total",
    "pps_index",
    "pps_numero",
    "pps_designacao",
    "work_project",
    "tecnologias_digitais",
    "tecnologias_ambientais",
    "num_tecnologias_digitais",
    "num_tecnologias_ambientais",
    "outra_digital",
    "outra_ambiental",
]

DETAIL_COLUMNS = [
    "timestamp",
    "company_id",
    "pps_numero",
    "pps_designacao",
    "work_project",
    "num_trabalhadores",
    "regiao",
    "categoria_tecnologia",
    "nome_tecnologia",
    "codigo_questao",
    "texto_questao",
    "resposta",
]
def get_credentials():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return creds
    
@st.cache_resource
def get_gspread_client():
    creds = get_credentials()
    return gspread.authorize(creds)


def get_main_worksheet():
    client = get_gspread_client()
    sh = client.open_by_key(MAIN_SPREADSHEET_ID)
    return sh.sheet1


def get_detail_worksheet():
    client = get_gspread_client()
    sh = client.open_by_key(DETAIL_SPREADSHEET_ID)
    return sh.sheet1


def save_main_rows_to_sheet(main_rows):
    ws = get_main_worksheet()
    for row_dict in main_rows:
        row = [row_dict.get(col, "") for col in MAIN_COLUMNS]
        ws.append_row(row, value_input_option="USER_ENTERED")


def save_detail_rows_to_sheet(detail_rows):
    ws = get_detail_worksheet()
    for row_dict in detail_rows:
        row = [row_dict.get(col, "") for col in DETAIL_COLUMNS]
        ws.append_row(row, value_input_option="USER_ENTERED")


st.set_page_config(page_title="Introduçao", layout="wide")

# ADD THIS CSS TO FIX TITLE DISPLAY
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    h1 {
        font-size: 1.8rem !important;
        line-height: 1.2 !important;
        word-wrap: break-word !important;
        margin-bottom: 1rem !important;
    }
    
    @media (max-width: 768px) {
        h1 {
            font-size: 1.4rem !important;
        }
    }
    
    header[data-testid="stHeader"] {
        height: 0px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Introduçao")

st.markdown("""
Este questionário tem como objetivo analisar em que medida as tecnologias consideradas
cruciais pela política industrial europeia, no contexto do acompanhamento dos
ecossistemas industriais da UE, estão presentes ou a ser desenvolvidas nos
**PPS** do consórcio Produtech R3.

Para cada PPS indicado, iremos identificar se e como estas tecnologias são
incorporadas no produto, bem como o seu grau de maturidade e de utilização.
""")


valid_steps = {0, 1, 2, 3}

if "step" not in st.session_state or st.session_state.step not in valid_steps:
    st.session_state.step = 0

if "company" not in st.session_state:
    st.session_state.company = {}

if "responses" not in st.session_state:
    st.session_state.responses = []

if "current_product_index" not in st.session_state:
    st.session_state.current_product_index = 0

if "n_products" not in st.session_state:
    st.session_state.n_products = 0

def save_survey_data_improved(company, responses, pps_data):
    """
    Save survey data in two CSV files:
    1. Main summary file with overview
    2. Detailed file with all question-answer pairs (WITH QUESTION TEXT)
    
    Generates unique sequential company_id for grouping responses
    """
    
    ts = datetime.now().isoformat()
    
    # ========== GENERATE UNIQUE COMPANY ID ==========
    # Sequential numbering: COMP_0001, COMP_0002, etc.
    # Each company submission gets a new unique number
    company_number_file = "last_company_number.txt"
    
    try:
        # Read the last company number
        if os.path.exists(company_number_file):
            with open(company_number_file, 'r') as f:
                last_number = int(f.read().strip())
        else:
            last_number = 0
        
        # Increment and assign to this company
        current_number = last_number + 1
        company_id = f"COMP_{current_number:04d}"  # Format: COMP_0001, COMP_0002, etc.
        
        # Save the new number for next submission
        with open(company_number_file, 'w') as f:
            f.write(str(current_number))
            
    except Exception as e:
        # Fallback: use timestamp-based ID if file operations fail
        import time
        timestamp_id = int(time.time() * 1000) % 100000  # Last 5 digits of millisecond timestamp
        company_id = f"COMP_{timestamp_id:05d}"
        print(f"Warning: Could not access company number file. Using timestamp-based ID: {company_id}")
    
    # ========== QUESTION TEXT MAPPING ==========
    QUESTION_TEXT_MAP = {
        # Blockchain
        "bc1": "BC-1. Como é utilizada a tecnologia blockchain no produto que está a desenvolver ou testar?",
        "bc1_out": "BC-1. Especificar outro",
        "bc2": "BC-2. Que tipo de tecnologia blockchain está integrada neste produto?",
        "bc3": "BC-3. Em que fase de desenvolvimento ou teste se encontra o componente de blockchain deste produto?",
        "bc4": "BC-4. Que funcionalidades ou processos dependem do blockchain no seu produto?",
        "bc4_out": "BC-4. Especificar outro",
        "bc5": "BC-5. Em que medida o componente de blockchain está ligado a outros sistemas?",
        
        # IoT
        "iot1": "IoT-1. Em que partes do produto/serviço são utilizadas soluções de Internet das Coisas?",
        "iot1_out": "IoT-1. Especificar outro",
        "iot2": "IoT-2. Aproximadamente que percentagem das funcionalidades principais do produto depende de IoT?",
        "iot3": "IoT-3. Em termos de dados utilizados pelo produto, que proporção estima que seja gerada por dispositivos IoT?",
        "iot4": "IoT-4. Quão crítica é a IoT para o funcionamento do produto?",
        "iot5": "IoT-5. Em que fase de desenvolvimento ou implementação está a componente de IoT neste produto?",
        
        # Computação em Nuvem
        "cn1": "CN-1. Quais as funções do seu produto que dependem de tecnologias de computação em nuvem?",
        "cn1_out": "CN-1. Especificar outro",
        "cn2": "CN-2. Em que fase está implementada a funcionalidade de nuvem neste produto?",
        "cn3": "CN-3. Que tipo de arquitetura melhor descreve o uso de nuvem no seu produto?",
        "cn4": "CN-4. Em que medida a sua solução de nuvem está integrada com outros sistemas?",
        
        # Robótica
        "rb1": "RB-1. Como é utilizada a robótica no produto ou solução desenvolvida/testada no âmbito do Produtech R3?",
        "rb1_out": "RB-1. Especificar",
        "rb2": "RB-2. Que tipos de robôs integram este produto?",
        "rb2_out": "RB-2. Especificar",
        "rb3": "RB-3. Em que fase de desenvolvimento ou teste se encontra o componente robótico deste produto?",
        "rb4": "RB-4. Como está a robótica integrada com o resto do sistema?",
        "rb5": "RB-5. Qual é o grau de autonomia do componente robótico?",
        "rb6": "RB-6. Que tipo de segurança ou funcionalidades colaborativas estão integradas?",
        
        # IA & Big Data
        "ia1": "IA-1. De que forma a IA está presente no produto que está a desenvolver ou testar?",
        "ia1_out": "IA-1. Especificar outro",
        "ia2": "IA-2. Que tipos de tecnologias ou algoritmos de IA estão integrados?",
        "ia2_out": "IA-2. Especificar outro",
        "ia3": "IA-3. Em que fase de desenvolvimento ou teste está o componente de IA neste produto?",
        "ia4": "IA-4. Que tipo de dados são utilizados para treinar ou operar o componente de IA?",
        "ia4_out": "IA-4. Especificar outro",
        "ia5": "IA-5. Em que medida o componente de IA está integrado com outros sistemas?",
        
        # RA/RV
        "rav1": "RAV-1. Como é que RA/RV está presente no produto que está a desenvolver ou testar?",
        "rav1_out": "RAV-1. Especificar outro", 
        "rav2": "RAV-2. Que tipo de tecnologia de RA ou RV está integrada?",
        "rav3": "RAV-3. Em que fase de desenvolvimento ou teste está o componente RA/RV?",
        "rav4": "RAV-4. Como é que os utilizadores interagem com o componente RA/RV?",
        "rav5": "RAV-5. Em que medida o componente RA/RV está integrado com outros sistemas?",
        "rav5_out": "RAV-5. Especificar outro",
        
        # Micro/Nanoeletrónica e Fotónica
        "mnf1": "MNF-1. De que forma componentes micro-, nanoeletrónicos ou fotónicos estão presentes no produto?",
        "mnf1_out": "MNF-1. Especificar outro",
        "mnf2": "MNF-2. Que tipos de tecnologias de micro-, nanoeletrónica ou fotónica estão integradas?",
        "mnf2_out": "MNF-2. Especificar outro",
        "mnf3": "MNF-3. Em que fase de desenvolvimento ou teste está o componente integrado no produto?",
        "mnf4": "MNF-4. Como foram estes componentes integrados no produto?",
        "mnf4_orig": "MNF-4. Origem do principal fornecedor",
        "mnf5": "MNF-5. Qual é a principal finalidade destes componentes?",
        "mnf5_out": "MNF-5. Especificar outro",
        
        # Edge Computing
        "ec1": "EC-1. Como é utilizado edge computing no produto que está a desenvolver ou testar?",
        "ec1_out": "EC-1. Especificar outro",
        "ec2": "EC-2. Em que fase está implementado o componente de edge computing?",
        "ec3": "EC-3. De que tipo de infraestrutura ou configuração edge depende este produto?",
        "ec3_out": "EC-3. Especificar outro",
        "ec4": "EC-4. Quais são as principais funções ou vantagens alcançadas com edge computing?",
        "ec4_out": "EC-4. Especificar outro",
        "ec5": "EC-5. Como está o componente edge integrado com outros sistemas?",
        
        # Cibersegurança
        "cs1": "CS-1. Como é que a cibersegurança está presente no produto que está a desenvolver ou testar?",
        "cs1_out": "CS-1. Especificar outro",
        "cs2": "CS-2. Em que fase de desenvolvimento ou teste está a funcionalidade de cibersegurança?",
        "cs3": "CS-3. Que aspetos do produto ou sistema estão protegidos através de cibersegurança?",
        "cs3_out": "CS-3. Especificar outro",
        "cs4": "CS-4. Que frameworks ou práticas orientam a implementação de cibersegurança?",
        
        # Materiais Avançados
        "ma1": "MA-1. De que forma os materiais avançados estão presentes no produto?",
        "ma1_out": "MA-1. Especificar outro",
        "ma2": "MA-2. Que tipos de materiais avançados estão integrados neste produto?",
        "ma2_out": "MA-2. Especificar outro",
        "ma3": "MA-3. Em que fase de desenvolvimento ou teste estão estes materiais integrados no produto?",
        "ma4": "MA-4. De onde provêm principalmente os materiais avançados deste produto?",
        "ma5": "MA-5. Qual é a principal função dos materiais avançados neste produto?",
        "ma5_out": "MA-5. Especificar outro",
        
        # Biotecnologia
        "bio1": "BIO-1. Como está a biotecnologia presente no produto que está a desenvolver ou testar?",
        "bio1_out": "BIO-1. Especificar outro",
        "bio2": "BIO-2. Que tipo(s) de biotecnologia ou processos biológicos estão integrados?",
        "bio2_out": "BIO-2. Especificar outro",
        "bio3": "BIO-3. Em que fase de desenvolvimento ou teste está a componente de biotecnologia?",
        "bio4": "BIO-4. De onde provêm os inputs biológicos ou tecnologia utilizada?",
        "bio5": "BIO-5. Qual é o principal objetivo ou benefício do componente de biotecnologia?",
        "bio5_out": "BIO-5. Especificar outro",
        
        # Reciclagem
        "rcu1": "RCU-1. Como está a reciclagem presente no produto que está a desenvolver ou testar?",
        "rcu1_out": "RCU-1. Especificar outro",
        "rcu2": "RCU-2. Que tipo(s) de reciclagem ou utilização circular de materiais fazem parte deste produto?",
        "rcu2_out": "RCU-2. Especificar outro",
        "rcu3": "RCU-3. Em que fase de desenvolvimento ou teste estão integradas as práticas de reciclagem?",
        "rcu4": "RCU-4. De onde provêm os materiais ou componentes reciclados utilizados neste produto?",
        "rcu5": "RCU-5. Qual é o principal objetivo ou valor acrescentado do componente de reciclagem?",
        "rcu5_out": "RCU-5. Especificar outro",
        
        # Poupança de Energia
        "tpe1": "TPE-1. Como estão as tecnologias de poupança de energia presentes no produto?",
        "tpe1_out": "TPE-1. Especificar outro",
        "tpe2": "TPE-2. Que tipo(s) de tecnologias de eficiência energética estão integradas?",
        "tpe2_out": "TPE-2. Especificar outro",
        "tpe3": "TPE-3. Em que fase de desenvolvimento ou teste estão estas tecnologias?",
        "tpe4": "TPE-4. Qual é a redução estimada de consumo de energia ou melhoria de eficiência?",
        "tpe5": "TPE-5. Qual é o principal objetivo das tecnologias de poupança de energia?",
        "tpe5_out": "TPE-5. Especificar outro",
        
        # Modelos Circulares
        "mcn1": "MCN-1. Como estão os modelos de negócio circulares presentes no produto?",
        "mcn1_out": "MCN-1. Especificar outro",
        "mcn2": "MCN-2. Que tipo(s) de estratégias circulares estão integradas?",
        "mcn2_out": "MCN-2. Especificar outro",
        "mcn3": "MCN-3. Em que fase de desenvolvimento ou implementação está o modelo de negócio?",
        "mcn4": "MCN-4. Como funciona o fluxo de materiais ou produtos no modelo circular?",
        "mcn5": "MCN-5. Qual é o principal objetivo ou benefício do modelo de negócio circular?",
        "mcn5_out": "MCN-5. Especificar outro",
        
        # Produção Limpa
        "tpl1": "TPL-1. Como estão as tecnologias de produção limpa presentes no produto?",
        "tpl1_out": "TPL-1. Especificar outro",
        "tpl2": "TPL-2. Que tipo(s) de tecnologias ou práticas de produção limpa estão integradas?",
        "tpl2_out": "TPL-2. Especificar outro",
        "tpl3": "TPL-3. Em que fase de desenvolvimento ou implementação estão estas tecnologias?",
        "tpl4": "TPL-4. Qual é a redução estimada de emissões ou impactos ambientais?",
        "tpl5": "TPL-5. Qual é o principal objetivo das tecnologias de produção limpa?",
        "tpl5_out": "TPL-5. Especificar outro",
        
        # Captura de Carbono
        "tcc1": "TCC-1. Como estão as tecnologias de captura ou redução de carbono presentes?",
        "tcc1_out": "TCC-1. Especificar outro",
        "tcc2": "TCC-2. Que tipo(s) de tecnologias de captura ou redução de CO₂ estão integradas?",
        "tcc2_out": "TCC-2. Especificar outro",
        "tcc3": "TCC-3. Em que fase de desenvolvimento ou teste estão estas tecnologias?",
        "tcc4": "TCC-4. Qual é a quantidade estimada de CO₂ capturado ou reduzido?",
        "tcc5": "TCC-5. Qual é o principal objetivo das tecnologias de captura de carbono?",
        "tcc5_out": "TCC-5. Especificar outro",
        
        # Energias Renováveis
        "ier1": "IER-1. Como está a integração de energias renováveis presente no produto?",
        "ier1_out": "IER-1. Especificar outro",
        "ier2": "IER-2. Que tipo(s) de energias renováveis estão integradas?",
        "ier2_out": "IER-2. Especificar outro",
        "ier3": "IER-3. Em que fase de desenvolvimento ou implementação está a integração?",
        "ier4": "IER-4. Qual é a percentagem de energia renovável no consumo total?",
        "ier5": "IER-5. Qual é o principal objetivo da integração de energias renováveis?",
        "ier5_out": "IER-5. Especificar outro",
    }
    
    # ========== FILE 1: MAIN SUMMARY (RIGHE MULTIPLE, STESSE COLONNE) ==========
    
    main_rows = []

    for i, r in enumerate(responses):
        # Get PPS info
        pps_info = r.get("pps_info", {})
        pps_num = pps_info.get("pps_num", "")
        pps_designation = pps_info.get("designation", "")
        wp = r.get("work_project", "")
    
        # Technology lists
        tech_dig = r.get("tech_digitais", [])
        tech_amb = r.get("tech_ambientais", [])
        
        # Trova il numero massimo di tecnologie per determinare quante righe servono
        max_technologies = max(len(tech_dig), len(tech_amb), 1)  # Minimo 1 riga
        
        # Crea una riga per ogni "slot" di tecnologia
        for tech_index in range(max_technologies):
            
            # Tecnologia digitale per questa riga (se esiste)
            current_tech_dig = tech_dig[tech_index] if tech_index < len(tech_dig) else ""
            
            # Tecnologia ambientale per questa riga (se esiste)  
            current_tech_amb = tech_amb[tech_index] if tech_index < len(tech_amb) else ""
            
            # Se entrambe sono vuote per questa riga, metti "Nenhuma"
            display_tech_dig = current_tech_dig if current_tech_dig else ("Nenhuma" if tech_index == 0 and not tech_dig else "")
            display_tech_amb = current_tech_amb if current_tech_amb else ("Nenhuma" if tech_index == 0 and not tech_amb else "")
            
            main_rows.append({
                "timestamp": ts,
                "company_id": company_id,
                "num_trabalhadores": company["num_trabalhadores"],
                "tipo_organizacao": ", ".join(company["tipo_organizacao"])
                if isinstance(company["tipo_organizacao"], list)
                else company["tipo_organizacao"],
                "regiao": company["regiao"],
                "num_pps_total": company["num_pps"],
                "pps_index": i + 1,
                "pps_numero": pps_num,
                "pps_designacao": pps_designation,
                "work_project": wp,
                "tecnologias_digitais": display_tech_dig,
                "tecnologias_ambientais": display_tech_amb,
                "num_tecnologias_digitais": len(tech_dig),
                "num_tecnologias_ambientais": len(tech_amb),
                "outra_digital": r.get("outra_digital", ""),
                "outra_ambiental": r.get("outra_ambiental", ""),
            })

    save_main_rows_to_sheet(main_rows)
    main_file = "google_sheets_resumo"
    
    # ========== FILE 2: DETAILED RESPONSES (LONG FORMAT WITH QUESTION TEXT) ==========

    detail_rows = []

    for i, r in enumerate(responses):
        # Get PPS info
        pps_info = r.get("pps_info", {})
        pps_num = pps_info.get("pps_num", "")
        pps_designation = pps_info.get("designation", "")

        # Base info common to all rows for this PPS
        base_info = {
            "timestamp": ts,
            "company_id": company_id,
            "pps_numero": pps_num,
            "pps_designacao": pps_designation,
            "work_project": r.get("work_project", ""),
            "num_trabalhadores": company["num_trabalhadores"],
            "regiao": company["regiao"],
        }

        detalhes_tech = r.get("detalhes_tech", {})

        for tech_name, tech_data in detalhes_tech.items():
            tech_digitais = r.get("tech_digitais", [])
            tech_ambientais = r.get("tech_ambientais", [])

            if tech_name in tech_digitais:
                tech_category = "Digital"
            elif tech_name in tech_ambientais:
                tech_category = "Ambiental"
            else:
                tech_category = "Outra"

            for question_key, answer_value in tech_data.items():
                question_text = QUESTION_TEXT_MAP.get(question_key, question_key)

                if isinstance(answer_value, list) and len(answer_value) > 0:
                    # one row per selected answer
                    for single_answer in answer_value:
                        if single_answer:
                            detail_rows.append(
                                {
                                    **base_info,
                                    "categoria_tecnologia": tech_category,
                                    "nome_tecnologia": tech_name,
                                    "codigo_questao": question_key,
                                    "texto_questao": question_text,
                                    "resposta": str(single_answer),
                                }
                            )
                else:
                    answer_str = str(answer_value) if answer_value else ""
                    detail_rows.append(
                        {
                            **base_info,
                            "categoria_tecnologia": tech_category,
                            "nome_tecnologia": tech_name,
                            "codigo_questao": question_key,
                            "texto_questao": question_text,
                            "resposta": answer_str,
                        }
                    )

    # 👉 invece del CSV:
    save_detail_rows_to_sheet(detail_rows)
    detail_file = "google_sheets_detalhes"

    return main_file, detail_file, company_id

    
PPS_DATA = {
    1: {"designation": "Plataforma de software PLM", "wp": "WP2"},
    2: {"designation": "Lean DfX Software", "wp": "WP2"},
    3: {"designation": "Equipamento mecatrónico Desafios em Sintonía – setor saúde, equipamento de proteção individual", "wp": "WP2"},
    4: {"designation": "Equipamento mecatrónico CEI setor rochas ornamentais", "wp": "WP2"},
    5: {"designation": "Equipamento mecatrónico JPM setor intralogística", "wp": "WP2"},
    6: {"designation": "Plataforma As-a-Service low code de configuração e parametrização do digital twin da fábrica", "wp": "WP3"},
    7: {"designation": "Serviços de desenho, configuração, operacionalização e melhoria contínua de fábricas I4.0", "wp": "WP3"},
    8: {"designation": "Solução tecnica complexa de manipulação e posicionamento de materiais especiais", "wp": "WP4"},
    9: {"designation": "Molde multifuncional para sobreinjeção de materiais fibrosos termoformáveis, flexíveis e permeáveis, com geometrias complexas, um caso especial de \"in- mould assembling\"", "wp": "WP4"},
    10: {"designation": "Equipamento modular de estampagem", "wp": "WP5"},
    11: {"designation": "Ferramenta inteligente de estampagem", "wp": "WP5"},
    12: {"designation": "Ferramentas inteligentes de soldadura por fricção linear (FSWI)", "wp": "WP5"},
    13: {"designation": "Ferramenta inteligente de abertura de canais internos por fricção (FSCI)", "wp": "WP5"},
    14: {"designation": "Moldes de elevado rendimento com canais FSC conformes", "wp": "WP5"},
    15: {"designation": "Plataforma Digital de Gestão e Monitorização de Dados", "wp": "WP6"},
    16: {"designation": "CompactPack – Célula Robótica Compacta, Flexível e Autoportante para Fins de Linha", "wp": "WP6"},
    17: {"designation": "Solução Robótica de Paletização de Produtos Irregulares", "wp": "WP6"},
    18: {"designation": "Ferramentas de controlo de qualidade adaptáveis para sistemas de embalamento flexíveis", "wp": "WP7"},
    19: {"designation": "Sistema de otimização de recursos e garantia de integridade no setor alimentar", "wp": "WP7"},
    20: {"designation": "Sistema de otimização de recursos para produção de artigos de cortiça de elevada qualidade", "wp": "WP7"},
    21: {"designation": "RAILES: plataforma de gestão inteligente em tempo-real de linhas de produção", "wp": "WP7"},
    23: {"designation": "MES (Manufacturing Execution System) Inteligente, Intuitivo e Visual", "wp": "WP8"},
    24: {"designation": "Veículo elétrico e autónomo desenvolvido para operar em contextos industriais fazendo a logística indoor/outdoor", "wp": "WP8"},
    25: {"designation": "Alimentação de linha eficiente e inteligente", "wp": "WP8"},
    26: {"designation": "Sistema otimizado para gestão de frotas de AGV´s independentemente da sua localização, indoor-outdoor", "wp": "WP8"},
    27: {"designation": "Armazém eficiente e inteligente", "wp": "WP8"},
    29: {"designation": "Soluções Robóticas Móveis para Movimentação de Produtos no Chão de Fábrica - AMRs", "wp": "WP9"},
    30: {"designation": "Empilhadores autónomos, com controlo remoto, para processos de carga e descarga de paletes", "wp": "WP9"},
    31: {"designation": "Sistemas Flexíveis de Paletização Robotizada", "wp": "WP9"},
    32: {"designation": "Sistemas robóticos modulares e flexíveis de suporte às operações de assemblagem", "wp": "WP9"},
    33: {"designation": "Solução robótica flexível para a formação de kits de peças", "wp": "WP9"},
    34: {"designation": "AMR Seguidor e abastecedor de linha de produção", "wp": "WP9"},
    35: {"designation": "Armazém Inteligente 5.0", "wp": "WP9"},
    36: {"designation": "Plataforma de planeamento e sequenciamento de tarefas de logística", "wp": "WP9"},
    37: {"designation": "Modelo Preditivo de Manutenção aplicando analítica de dados", "wp": "WP9"},
    38: {"designation": "Gestão e Sincronização de necessidades de abastecimento", "wp": "WP9"},
    39: {"designation": "Sorter de alta cadência", "wp": "WP9"},
    40: {"designation": "Quantificação volumétrica em camiões e máquinas de descarga", "wp": "WP9"},
    41: {"designation": "Auditor Virtual de Qualidade", "wp": "WP9"},
    42: {"designation": "Software para digitalização e rastreabilidade total dos processos logísticos baseado em Digital Twin e animação 3D", "wp": "WP9"},
    43: {"designation": "Software de apoio à tomada de decisão baseado em Simulação para otimização dos processos baseado em Digital Twin", "wp": "WP9"},
    44: {"designation": "Solução de rede privada/dedicada 5G para aplicação industrial", "wp": "WP9"},
    45: {"designation": "Plataforma digital de apoio à gestão de iniciativas Lean Manufacturing - Lean 4.0", "wp": "WP9"},
    46: {"designation": "Smart PLM e Paperless (Smart PLM para Operações de Manutenção de Produtos Complexos)", "wp": "WP9"},
    47: {"designation": "Sistema de realidade aumentada para apoio em tarefas complexas e rastreabilidade em indústrias de manutenção e reparação", "wp": "WP9"},
    48: {"designation": "Sistema de inspeção para teares com inspeção 100% dos tecidos produzidos", "wp": "WP9"},
    49: {"designation": "Software de inteligência artificial e advanced analytics para o desenho e configuração de sistemas produtivos e logísticos", "wp": "WP9"},
    50: {"designation": "Software de inteligência artificial e advanced analytics para o planeamento e operação de sistemas produtivos", "wp": "WP9"},
    51: {"designation": "Sistema de realidade aumentada para formação e apoio aos operadores em sistemas de assemblagem complexo", "wp": "WP9"},
    52: {"designation": "Novo sistema de Otimização de matéria- prima (Nesting) aplicado à indústria das Rochas Ornamentais", "wp": "WP9"},
    53: {"designation": "Software de Otimização de escalonamento e sequenciamento da produção", "wp": "WP10"},
    54: {"designation": "Software (API) integração dos fluxos de informação", "wp": "WP10"},
    55: {"designation": "Software Setup Automático", "wp": "WP10"},
    56: {"designation": "Modelo de Simulação (Software) com a representação digital dos processos industriais", "wp": "WP10"},
    57: {"designation": "Modelo de Simulação (Software) com a representação do sistema de Armazenamento automático, flexível e adaptativo", "wp": "WP10"},
    58: {"designation": "Sistema de gestão de armazéns automatizado e adaptável", "wp": "WP10"},
    59: {"designation": "Sistema inteligente de ajuste automático dinâmico dos consumos de energia elétrica (Software)", "wp": "WP10"},
    60: {"designation": "Sistema de apoio à decisão para processo de fabrico RTM (SmaRTM-DSS)", "wp": "WP11"},
    61: {"designation": "Sistema integrado de monitorização e controlo para processos de fabrico RTM", "wp": "WP11"},
    62: {"designation": "Fábrica para Extração de Bioativos e Biocompósitos (curcumina e nanocelulose)", "wp": "WP12"},
    63: {"designation": "DigiUpdate – Digitalização e sensorização avançada de equipamentos de composição para processamento de biocompósitos", "wp": "WP12"},
    64: {"designation": "OZOHealth – Gerador de Ozono assistido com ultrassons para fluidos viscosos", "wp": "WP12"},
    65: {"designation": "Plataforma IoT flexível e Plug and Play (plataforma integrada para melhoria da sensorização, integração e exploração de fluxos de dados)", "wp": "WP13"},
    66: {"designation": "Módulo de Eficiência Energética e Sustentabilidade", "wp": "WP13"},
    67: {"designation": "Módulo de Manutenção Preditiva para melhoria da disponibilidade e eficiência de equipamentos", "wp": "WP13"},
    68: {"designation": "Roteiros Setoriais e Guias Metodológicos para Descarbonização da Indústria", "wp": "WP14"},
    69: {"designation": "Ferramenta para otimização e gestão de sistemas holísticos de fornecimento, armazenamento e gestão de energia térmica com base em fontes de energias renováveis", "wp": "WP14"},
    70: {"designation": "Ferramentas avançadas de gestão de energia com ligação ao planeamento industrial", "wp": "WP14"},
    71: {"designation": "Soluções para retrofiting de queimadores para adaptação a gases renováveis", "wp": "WP14"},
    72: {"designation": "Sistemas de armazenamento de energia térmica e soluções tecnológicas de armazenamento de energia, recuperação de calor residual e integração energética", "wp": "WP14"},
    73: {"designation": "Soluções de Sensorização para a caracterização de misturas (blend) de Gás Natural e Hidrogénio e para caracterização de efluentes gasosos", "wp": "WP14"},
    74: {"designation": "Soluções de tratamento de efluentes industriais para alimentação de água a centrais de produção de hidrogénio verde", "wp": "WP14"},
    75: {"designation": "Plataforma tecnológica Biomassa para a indústria", "wp": "WP14"},
    76: {"designation": "Smart-Objects Sensores facilitadores para a digitalização", "wp": "WP15"},
    77: {"designation": "Familia de produtos All-Synergy – Módulos Orientados a Supra- Indicadores, Advanced Sustainability Reporting", "wp": "WP15"},
    78: {"designation": "Módulo All-Synergy CircProsys", "wp": "WP15"},
    79: {"designation": "Vanguarda MarketPlace SW", "wp": "WP15"},
    80: {"designation": "Vanguarda Lean & Green 4.0 SW", "wp": "WP15"},
    81: {"designation": "Máquina Segregação materiais", "wp": "WP15"},
    82: {"designation": "Plataforma escalável para valorização e extensão do Ciclo de Vida de Equipamentos Industriais ativos empresariais", "wp": "WP16"},
    83: {"designation": "Sistema de Logística interna", "wp": "WP16"},
    84: {"designation": "Equipamento de conformação plástica de materiais metálicos", "wp": "WP16"},
    85: {"designation": "Equipamento de corte de pedra", "wp": "WP16"},
    86: {"designation": "Centro de Maquinagem", "wp": "WP16"},
    87: {"designation": "Equipamento de Processamento de pele", "wp": "WP16"},
}

# Macro areas structure
MACRO_AREAS = {
   'A - Personalização de Produto e Produção de Proximidade (WP2-WP3)': ['WP2', 'WP3'],
   'B - Produção Adaptativa, Colaborativa e Competitiva (WP5-WP7)': ['WP4', 'WP5', 'WP6', 'WP7'],
   'C - Sistema de Produção Interoperável (WP8-WP10)': ['WP8', 'WP9', 'WP10'],
   'D - Novas Tecnologias de Produção e Materiais Avançados (WP11-WP12)': ['WP11', 'WP12'],
   'E - Eficiência de Recursos e Energia e Renováveis (WP13-WP16)': ['WP13', 'WP14', 'WP15', 'WP16']
}

def get_macro_area_for_wp(wp):
    """Get macro area for a given WP"""
    for macro_area, wps in MACRO_AREAS.items():
        if wp in wps:
            return macro_area
    return "Unknown"

def get_pps_by_wp(wp):
    """Get all PPS for a given WP"""
    return {pps_num: data for pps_num, data in PPS_DATA.items() if data['wp'] == wp}

# SECTION I
def render_section_1():
    st.title("Questionário Produtech R3")
    st.header("SECÇÃO I – Identificação e Classificação")
    st.write("Esta secção recolhe informações básicas para classificar as respostas por área, tipo de organização e região.")

    # 1. Tipo de Organização (moved to top)
    tipo_org = st.radio("1. Tipo de Organização (selecione todas as opções aplicáveis)", [
        "Empresa privada – Desenvolvedora (desenvolvimento ativo de novo produto, serviço ou processo)",
        "Empresa privada – Utilizadora (testa, adota ou aplica tecnologias desenvolvidas)",
        "Organização de Investigação e Tecnologia (OIT), Associação ou Universidade"
    ], key="tipo_org")
    
    # 2. Número de Trabalhadores (conditional - only for companies)
    num_trab = None
    if tipo_org and "Organização de Investigação e Tecnologia (OIT), Associação ou Universidade" not in tipo_org:
        num_trab = st.radio("2. Número de Trabalhadores", [
            "Menos de 10 (microempresa)",
            "10–49 (pequena empresa)",
            "50–249 (média empresa)",
            "250 ou mais (grande empresa)"
        ], key="num_trab")
    else:
        # For universities/research organizations, set a default value or "N/A"
        num_trab = "N/A - Organização de Investigação"
    
    # 3. Região Principal de Operação
    regiao = st.radio("3. Região Principal de Operação (NUTS II)",
        ["Norte", "Centro", "Lisboa", "Alentejo", "Algarve", "Açores", "Madeira"],
        key="regiao")
    
    st.write("---")
    
    # 4. PPS Selection
    st.subheader("4. PPS Contribuídos no âmbito do Produtech R3")
    st.write("""
**Selecione os produtos, sistemas ou demonstradores que a sua organização contribuiu para desenvolver ou testar.**  
Para cada registo, comece por escolher a **Macro-área**, em seguida selecione o **Work Package (WP)** correspondente e, por fim, o **PPS específico**. Esta sequência permite classificar melhor a informação e associar cada conjunto de respostas ao produto, sistema ou demonstrador certo.

Depois de **confirmar e adicionar um PPS à lista**, as barras de seleção mantêm as escolhas anteriores. Se quiser adicionar um **novo PPS**, terá de voltar a ajustar a Macro-área, o WP e o PPS antes de o confirmar novamente.
""")
    
    # Initialize session state for PPS selections
    if 'selected_pps' not in st.session_state:
        st.session_state.selected_pps = []
    
    # Show current selections first (if any)
    if st.session_state.selected_pps:
        st.success(f"✅ **{len(st.session_state.selected_pps)} PPS selecionado(s)**")
        
        for i, pps in enumerate(st.session_state.selected_pps):
            with st.expander(f"PPS {pps['pps_num']}: {pps['designation'][:80]}...", expanded=False):
                st.write(f"**Designação completa:** {pps['designation']}")
                st.write(f"**Macro Área:** {pps['macro_area']}")
                st.write(f"**Work Project:** {pps['wp']}")
                
                if st.button("🗑️ Remover este PPS", key=f"remove_pps_{i}"):
                    st.session_state.selected_pps.pop(i)
                    st.rerun()
        
        st.write("---")
    
    # Option to add more PPS
    st.subheader("➕ Adicionar novo PPS")
    
    # Step 1: Select Macro Area
    macro_area = st.selectbox(
        "**Passo 1:** Selecione a Macro Área:",
        options=[""] + list(MACRO_AREAS.keys()),
        key="macro_area_select"
    )
    
    if macro_area:
        # Step 2: Select WP within the macro area
        available_wps = MACRO_AREAS[macro_area]
        wp = st.selectbox(
            "**Passo 2:** Selecione o Work Package:",
            options=[""] + available_wps,
            key="wp_select"
        )
        
        if wp:
            # Step 3: Select PPS within the WP
            pps_in_wp = get_pps_by_wp(wp)
            
            if len(pps_in_wp) > 0:
                st.write(f"**Passo 3:** Selecione o PPS (disponíveis em {wp}: {len(pps_in_wp)})")
                
                # Create options
                pps_options = {}
                for pps_num, data in sorted(pps_in_wp.items()):
                    short_name = data['designation'][:100] + "..." if len(data['designation']) > 100 else data['designation']
                    display_name = f"PPS {pps_num}: {short_name}"
                    
                    pps_options[display_name] = {
                        'pps_num': pps_num,
                        'designation': data['designation'],
                        'wp': wp,
                        'macro_area': macro_area
                    }
                
                pps_choice = st.selectbox(
                    "Escolha o PPS:",
                    options=[""] + list(pps_options.keys()),
                    key="pps_select"
                )
                
                if pps_choice:
                    pps_data = pps_options[pps_choice]
                    
                    # Show full designation
                    st.info(f"**Designação completa:**\n\n{pps_data['designation']}")
                    
                    # Button to add
                    if st.button("✅ Confirmar e adicionar este PPS", key="add_pps_button", type="primary"):
                        if not any(p['pps_num'] == pps_data['pps_num'] for p in st.session_state.selected_pps):
                            st.session_state.selected_pps.append(pps_data)
                            st.success(f"PPS {pps_data['pps_num']} adicionado com sucesso!")
                            st.rerun()  
                        else:
                          st.warning("⚠️ Este PPS já foi adicionado à lista.")
    

    # Temporary debugging (remove after testing)
    with st.expander("🔍 Debug Info (temporary)", expanded=False):
        st.write(f"Number of PPS selected: {len(st.session_state.selected_pps)}")
        st.write(f"Selected PPS: {st.session_state.selected_pps}")
        st.write(f"tipo_org filled: {bool(tipo_org)}")
        st.write(f"regiao filled: {bool(regiao)}")
        st.write(f"num_trab filled: {bool(num_trab) if num_trab else 'N/A for OIT'}")
    
    
    
    
    
    # Navigation button
    st.write("---")

    # More explicit validation
    num_pps = len(st.session_state.selected_pps)

    if num_pps == 0:
        st.warning("⚠️ Por favor, adicione pelo menos um PPS antes de continuar.")
    elif num_pps == 1:
        st.info(f"✓ {num_pps} PPS selecionado. Pode prosseguir quando estiver pronto.")
    else:
        st.success(f"✓ {num_pps} PPS selecionados. Pode prosseguir quando estiver pronto.")

    # Check ALL required fields before enabling button
    can_proceed = (
        num_pps > 0 and 
        tipo_org and 
        regiao and
        (num_trab or "Organização de Investigação e Tecnologia (OIT), Associação ou Universidade" in tipo_org)
    )
# Additional validation before proceeding
    if st.button("Próximo ➡️", key="next_sec1", disabled=(not can_proceed), type="primary"):
        if not tipo_org or not regiao:
            st.error("❌ Por favor, preencha todos os campos obrigatórios.")
        elif num_pps == 0:
          st.error("❌ Por favor, adicione pelo menos um PPS.")
        else:
            st.session_state.company = {
             "num_trabalhadores": num_trab,
             "tipo_organizacao": tipo_org,
             "regiao": regiao,
             "selected_pps": st.session_state.selected_pps,
             "num_pps": num_pps
           }
           st.session_state.n_products = num_pps
           st.session_state.responses = [{} for _ in range(num_pps)]
           st.session_state.step = 1
           st.session_state.current_product_index = 0
           st.rerun()
# SECTION II - Product intro
def render_section_2_intro():
    idx = st.session_state.current_product_index
    n = st.session_state.n_products
    
    # Get the PPS info from Section I
    selected_pps = st.session_state.company['selected_pps'][idx]
    
    st.title(f"PPS {idx + 1} de {n}")
    st.header("SECÇÃO II – Tecnologias Digitais e Verdes")
    
    # Display PPS information
    st.markdown(f"""
    <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3;">
        <h4>📋 PPS Selecionado: PPS {selected_pps['pps_num']}</h4>
        <p><strong>Designação:</strong> {selected_pps['designation']}</p>
        <p><strong>Macro Área:</strong> {selected_pps['macro_area']}</p>
        <p><strong>Work Project:</strong> {selected_pps['wp']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    wp = selected_pps['wp']
    
    st.subheader("Tecnologias Digitais Integradas no Produto")
    st.write("Selecione todas as opções aplicáveis")
    
    tech_dig = st.multiselect("Tecnologias Digitais:", [
        "Inteligência Artificial e Big Data",
        "Robótica",
        "Computação em Nuvem (Cloud Computing)",
        "Internet das Coisas (IoT)",
        "Realidade Aumentada / Realidade Virtual (RA/RV)",
        "Blockchain",
        "Micro / Nanoeletrónica e Fotónica",
        "Edge Computing",
        "Cibersegurança",
        "Outra Inovação Digital"
    ], key=f"tech_dig_{idx}")
    
    outra_dig = ""
    if "Outra Inovação Digital" in tech_dig:
        outra_dig = st.text_input("Especificar:", key=f"outra_dig_{idx}")
    
    st.subheader("Tecnologias e Medidas Ambientais Integradas no Produto")
    st.write("Selecione todas as opções aplicáveis")
    
    tech_amb = st.multiselect("Tecnologias Ambientais:", [
        "Integração de Energias Renováveis",
        "Tecnologias de Poupança de Energia",
        "Materiais Avançados",
        "Aplicações de Biotecnologia",
        "Tecnologias de Produção Limpa",
        "Soluções de Reciclagem",
        "Tecnologias de Captura ou Redução de Carbono (CO₂)",
        "Modelos de Negócio Industriais Circulares",
        "Outra Inovação Ambiental"
    ], key=f"tech_amb_{idx}")
    
    outra_amb = ""
    if "Outra Inovação Ambiental" in tech_amb:
        outra_amb = st.text_input("Especificar:", key=f"outra_amb_{idx}")
    
    # Navigation buttons - mobile friendly
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("⬅️ Anterior", key="prev_intro", use_container_width=True):
                st.session_state.current_product_index -= 1
                st.rerun()
        elif st.button("⬅️ Voltar à Secção I", key="back_sec1", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    
    with col2:
        if st.button("Próximo ➡️", key="next_intro", use_container_width=True):
            if tech_dig or tech_amb:
                st.session_state.responses[idx] = {
                    "pps_info": selected_pps,
                    "work_project": wp,
                    "tech_digitais": tech_dig,
                    "tech_ambientais": tech_amb,
                    "outra_digital": outra_dig,
                    "outra_ambiental": outra_amb,
                    "detalhes_tech": {}
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("❌ Por favor, selecione pelo menos uma tecnologia.")

# ========== DIGITAL TECHNOLOGY FUNCTIONS ==========

def render_computacao_nuvem(idx):
    with st.expander("1. Computação em Nuvem (Cloud Computing) ", expanded=True):
        k = f"cn_{idx}"
        
        cn1 = st.multiselect("CN-1. Quais as funções do seu produto que dependem de tecnologias de computação em nuvem?", [
            "Armazenamento / gestão de dados",
            "Análise de dados / alojamento de modelos de IA",
            "Plataforma de gémeo digital ou simulação",
            "Interface de monitorização ou controlo remoto",
            "Portal web de cliente ou fornecedor",
            "API / partilha de dados com parceiros",
            "Outro"
        ], key=f"{k}_1")
        cn1_out = st.text_input("Especificar outro:", key=f"{k}_1o") if "Outro" in cn1 else ""
        
        cn2 = st.radio("CN-2. Em que fase está implementada a funcionalidade de nuvem neste produto?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado em uso produtivo"
        ], key=f"{k}_2")
        
        cn3 = st.multiselect("CN-3. Que tipo de arquitetura melhor descreve o uso de nuvem no seu produto?", [
            "Nuvem pública (ex.: Azure, AWS, Google Cloud)",
            "Nuvem privada (infraestrutura dedicada)",
            "Híbrida (nuvem + recursos locais)",
            "Configuração edge-to-cloud (processamento local + remoto)",
            "Não sabe / gerido por parceiro"
        ], key=f"{k}_3")
        
        cn4 = st.radio("CN-4. Em que medida a sua solução de nuvem está integrada com outros sistemas?", [
            "Independente (utilizada apenas no produto)",
            "Ligada a sistemas internos (ERP, MES, etc.)",
            "Ligada a sistemas de parceiros ou clientes para troca de dados",
            "Ligada a uma plataforma de dados partilhada do consórcio"
        ], key=f"{k}_4")
        
        return {
            "cn1": cn1,
            "cn1_out": cn1_out,
            "cn2": cn2,
            "cn3": cn3,
            "cn4": cn4
        }

def render_robotica(idx):
    with st.expander("2. Robótica", expanded=True):
        k = f"rb_{idx}"
        
        rb1 = st.multiselect("RB-1. Como é utilizada a robótica no produto ou solução desenvolvida/testada no âmbito do Produtech R3?", [
            "Funcionalidade principal do produto (ex.: célula robótica, estação de cobot, AGV/AMR)",
            "Componente integrado num sistema de produção mais amplo",
            "Sistema robótico utilizado para testes, montagem ou manuseamento durante a validação",
            "Robótica utilizada para inspeção, metrologia ou controlo de qualidade",
            "Outro"
        ], key=f"{k}_1")
        rb1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in rb1 else ""
        
        rb2 = st.multiselect("RB-2. Que tipos de robôs integram este produto?", [
            "Robôs industriais (fixos, articulados ou SCARA)",
            "Robôs colaborativos (cobots que trabalham com humanos)",
            "Robôs móveis / AGVs / AMRs",
            "Robôs especializados (ex.: soldadura, pintura, paletização)",
            "Robôs de serviço ou logística",
            "Outro"
        ], key=f"{k}_2")
        rb2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in rb2 else ""
        
        rb3 = st.radio("RB-3. Em que fase de desenvolvimento ou teste se encontra o componente robótico deste produto?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada junto de clientes",
            "Totalmente implementado e em utilização"
        ], key=f"{k}_3")
        
        rb4 = st.multiselect("RB-4. Como está o componente robótico integrado no restante ambiente de produção?", [
            "Opera como célula robótica independente",
            "Conectado a outras máquinas ou transportadores",
            "Integrado com sistemas de controlo (MES/ERP)",
            "Utiliza visão artificial, sensores ou IA para controlo adaptativo",
            "Espaço colaborativo homem-robô",
            "Ainda não integrado (testado isoladamente)"
        ], key=f"{k}_4")
        
        rb5 = st.multiselect("RB-5. Qual é a principal função do sistema robótico neste produto?", [
            "Manuseamento ou alimentação de materiais",
            "Montagem ou junção",
            "Embalagem ou paletização",
            "Inspeção de qualidade ou medição",
            "Automatização de processos (ex.: maquinação, soldadura, pintura)",
            "Intralogística ou automatização de armazém",
            "Outro"
        ], key=f"{k}_5")
        rb5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in rb5 else ""

           
        return{
            "rb1":rb1,
            "rb1_out":rb1_out,
            "rb2":rb2,
            "rb2_out":rb2_out,
            "rb3":rb3,
            "rb4":rb4,
            "rb5":rb5,
            "rb5_out":rb5_out
            }

def render_ia_bigdata(idx):
    with st.expander("3. Inteligência Artificial & Big Data", expanded=True):
        k = f"ia_{idx}"
        
        ia1 = st.multiselect("IA-1. De que forma a inteligência artificial ou a análise de dados está presente no produto que está a desenvolver ou testar?", [
            "Funcionalidade central do produto (ex.: sistema habilitado por IA, módulo inteligente)",
            "Componente de apoio ao controlo ou otimização do processo",
            "Utilizada para testes, inspeção de qualidade ou monitorização de desempenho",
            "Utilizada para analisar dados de produção ou prever necessidades de manutenção",
            "Utilizada para personalização ou comportamento adaptativo",
            "Outro"
        ], key=f"{k}_1")
        ia1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in ia1 else ""
        
        ia2 = st.radio("IA-2. Qual das seguintes opções descreve melhor a forma como a IA é utilizada neste produto?", [
            "O produto integra ferramentas de IA publicamente disponíveis (ex.: ChatGPT, Copilot, Bard)",
            "O produto integra soluções de IA de terceiros nos seus processos",
            "O produto inclui modelos ou sistemas de IA desenvolvidos internamente ou com parceiros OIT",
            "Não sabe / desenvolvido externamente por parceiros"
        ], key=f"{k}_2")
        
        ia3 = st.multiselect("IA-3. Que tipos de tecnologias de IA ou dados são aplicadas neste produto?", [
            "Machine Learning (modelos preditivos, deteção de anomalias)",
            "Deep Learning (interpretação de imagem / dados de sensores)",
            "Processamento de Linguagem Natural (chatbots, análise de texto ou voz)",
            "Visão por Computador (inspeção visual, reconhecimento de objetos)",
            "IA Generativa (criação de dados sintéticos, designs ou código)",
            "Automatização Robótica de Processos – RPA (automatização baseada em regras)",
            "Analítica Preditiva (previsão de procura, manutenção, energia)",
            "Sistemas de Recomendação (funcionalidades adaptativas ou personalizadas)",
            "Outro"
        ], key=f"{k}_3")
        ia3_out = st.text_input("Especificar:", key=f"{k}_3o") if "Outro" in ia3 else ""
        
        ia4 = st.radio("IA-4. Em que fase de desenvolvimento ou teste se encontra a funcionalidade de IA do produto?", [
            "Fase de conceito / design",
            "Protótipo em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / operacional"
        ], key=f"{k}_4")
        
        ia5 = st.multiselect("IA-5. De que fontes de dados e integrações depende o componente de IA?", [
            "Dados internos do produto ou de sensores",
            "Dados do processo produtivo",
            "Conjuntos de dados partilhados pelo consórcio / parceiros",
            "Conjuntos de dados externos (ex.: mercado, ambiente, cliente)",
            "Pipelines de dados na nuvem ou APIs"
        ], key=f"{k}_5")
        
        ia6 = st.multiselect("IA-6. Em que parte do produto ou processo a IA é aplicada?", [
            "Design de produto ou processo",
            "Fabrico / otimização de processo",
            "Controlo de qualidade ou deteção de defeitos",
            "Manutenção preditiva",
            "Eficiência energética ou de recursos",
            "Logística ou planeamento",
            "Interação com o utilizador ou apoio à decisão",
            "Outro"
        ], key=f"{k}_6")
        ia6_out = st.text_input("Especificar:", key=f"{k}_6o") if "Outro" in ia6 else ""
        
        return{
            "ia1":ia1,
            "ia1_out":ia1_out,
            "ia2":ia2,
            "ia3":ia3,
            "ia3_out":ia3_out,
            "ia4":ia4,
            "ia5":ia5,
            "ia6":ia6,
            "ia6_out":ia6_out
               }

def render_ra_rv(idx):
    with st.expander("4. Realidade Aumentada / Realidade Virtual (RA/RV)", expanded=True):
        k = f"rav_{idx}"
        
        rav1 = st.multiselect("RAV-1. Como é que a Realidade Aumentada ou Virtual está presente no produto que está a desenvolver ou testar?", [
            "Funcionalidade central do produto (ex.: plataforma RA/RV, módulo de visualização)",
            "Ferramenta de apoio à orientação do operador ou assistência à montagem",
            "Utilizada para simulação ou prototipagem digital",
            "Utilizada para formação ou desenvolvimento de competências",
            "Utilizada para demonstração, visualização ou vendas a clientes",
            "Utilizada para manutenção remota ou suporte técnico",
            "Outro"
        ], key=f"{k}_1")
        rav1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in rav1 else ""
        
        rav2 = st.multiselect("RAV-2. Que tipos de tecnologias de RA/RV estão integradas neste produto?", [
            "Realidade Aumentada (sobreposições digitais no ambiente real)",
            "Realidade Virtual (ambiente digital totalmente imersivo)",
            "Realidade Mista (interação entre elementos reais e virtuais)",
            "Visualização 3D em ecrã ou tablet (não imersiva)",
            "Outro"
        ], key=f"{k}_2")
        rav2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in rav2 else ""
        
        rav3 = st.radio("RAV-3. Em que fase de desenvolvimento ou teste se encontra o componente de RA/RV?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / operacional"
        ], key=f"{k}_3")
        
        rav4 = st.multiselect("RAV-4. Como é entregue a experiência de RA/RV neste produto?", [
            "Óculos / headsets de RA (ex.: HoloLens, Magic Leap)",
            "Headsets de RV (ex.: Oculus, HTC Vive)",
            "RA em tablet / smartphone",
            "Visualização em desktop ou ecrã",
            "Dispositivo vestível (wearable) ou sistema de sensores integrado",
            "Outro"
        ], key=f"{k}_4")
        rav4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in rav4 else ""
        
        rav5 = st.multiselect("RAV-5. Em que caso(s) de uso o componente de RA/RV acrescenta valor?", [
            "Design e validação de produto",
            "Formação de operadores ou simulação",
            "Orientação para montagem ou manutenção",
            "Suporte técnico remoto",
            "Layout virtual de fábrica ou simulação de processo",
            "Marketing / experiência do utilizador / demonstração a clientes",
            "Outro"
        ], key=f"{k}_5")
        rav5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in rav5 else ""
        
        return{
            "rav1":rav1,
            "rav1_out":rav1_out,
            "rav2":rav2,
            "rav2_out":rav2_out,
            "rav3":rav3,
            "rav4":rav4,
            "rav4_out":rav4_out,
            "rav5":rav5,
            "rav5_out":rav5_out
            }


def render_blockchain(idx):
    with st.expander("5. Blockchain", expanded=True):
        k = f"bc_{idx}"
        
        bc1 = st.multiselect("BC-1. Como é utilizada a tecnologia blockchain no produto que está a desenvolver ou testar?", [
            "Funcionalidade central do produto (ex.: plataforma ou serviço baseado em blockchain)",
            "Utilizada para rastrear e verificar dados de produção",
            "Utilizada para assegurar rastreabilidade de produto ou material",
            "Utilizada para gestão de smart contracts ou transações",
            "Utilizada para segurança e validação da partilha de dados entre parceiros",
            "Outro"
        ], key=f"{k}_1")
        bc1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in bc1 else ""
        
        bc2 = st.multiselect("BC-2. Que tipo de tecnologia blockchain está integrada neste produto?", [
            "Blockchain permissionado (acesso restrito a consórcio ou clientes)",
            "Blockchain público (rede aberta)",
            "Modelo híbrido (parcialmente público, parcialmente restrito)",
            "Registo distribuído ou alternativa (ex.: IOTA, Hyperledger, Corda)",
            "Não sabe / desenvolvido externamente por parceiro"
        ], key=f"{k}_2")
        
        bc3 = st.radio("BC-3. Em que fase de desenvolvimento ou teste se encontra o componente de blockchain deste produto?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada com utilizadores",
            "Totalmente implementado e operacional"
        ], key=f"{k}_3")
        
        bc4 = st.multiselect("BC-4. Que funcionalidades ou processos dependem do blockchain no seu produto?", [
            "Rastreabilidade do produto ao longo da cadeia de valor",
            "Verificação de certificados de sustentabilidade ou qualidade",
            "Integridade de dados / registo inviolável",
            "Smart contracts para transações automatizadas",
            "Tokenização ou representação digital de ativos",
            "Gestão de identidades ou controlo de acesso",
            "Outro"
        ], key=f"{k}_4")
        bc4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in bc4 else ""
        
        bc5 = st.radio("BC-5. Em que medida o componente de blockchain está ligado a outros sistemas?", [
            "Protótipo autónomo, ainda não ligado",
            "Integrado com sistemas internos da empresa (ERP, MES, etc.)",
            "Conectado a parceiros ou fornecedores do consórcio",
            "Ligado a clientes externos ou sistemas públicos"
        ], key=f"{k}_5")
        
        return{
            "bc1":bc1,
            "bc1_out":bc1_out,
            "bc2":bc2,
            "bc3":bc3,
            "bc4":bc4,
            "bc4_out":bc4_out,
            "bc5":bc5
            }


def render_micro_nano(idx):
    with st.expander("6. Micro / Nanoeletrónica e Fotónica", expanded=True):
        k = f"mnf_{idx}"
        
        mnf1 = st.multiselect("MNF-1. De que forma componentes micro-, nanoeletrónicos ou fotónicos estão presentes no produto que está a desenvolver ou testar?", [
            "Elemento nuclear do produto (ex.: módulo de deteção, controlo ou comunicação)",
            "Subcomponente integrado desenvolvido com parceiros ou fornecedores",
            "Utilizados para processamento de sinal ou aquisição de dados",
            "Utilizados para gestão ou conversão de energia",
            "Utilizados para imagem, medição ou comunicação ótica",
            "Outro"
        ], key=f"{k}_1")
        mnf1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in mnf1 else ""
        
        mnf2 = st.multiselect("MNF-2. Que tipos de tecnologias de micro-, nanoeletrónica ou fotónica estão integradas?", [
            "Sensores (temperatura, pressão, posição, químicos, óticos …)",
            "Microcontroladores / processadores embebidos",
            "Eletrónica de potência ou conversores",
            "Chips de comunicação RF / 5G / sem fios",
            "Dispositivos óticos ou fotónicos (lasers, LED, fibra ótica, lentes)",
            "Sistemas de imagem / visão ou fotodíodos",
            "MEMS / NEMS (sistemas micro ou nanoeletromecânicos)",
            "Outro"
        ], key=f"{k}_2")
        mnf2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in mnf2 else ""
        
        mnf3 = st.radio("MNF-3. Em que fase de desenvolvimento ou teste está o componente integrado no produto?", [
            "Fase de conceito / design",
            "Protótipo em condições de laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado em produto operacional"
        ], key=f"{k}_3")
        
        mnf4 = st.multiselect("MNF-4. Como foram estes componentes integrados no produto?", [
            "Componentes comerciais off-the-shelf",
            "Design personalizado pelo fornecedor ou parceiro",
            "Codesenvolvido com OIT / organização de investigação",
            "Desenvolvido integralmente in-house"
        ], key=f"{k}_4")
        
        mnf4_orig = st.radio("Origem do principal fornecedor:", [
            "Portugal",
            "UE27",
            "Fora da UE",
            "Não sabe"
        ], key=f"{k}_4o")
        
        mnf5 = st.multiselect("MNF-5. Qual é a principal finalidade destes componentes?", [
            "Deteção / monitorização",
            "Controlo e automatização",
            "Comunicação e conectividade",
            "Gestão ou conversão de energia",
            "Medição e garantia da qualidade",
            "Transmissão ótica / iluminação",
            "Outro"
        ], key=f"{k}_5")
        mnf5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in mnf5 else ""
        
        return{"mnf1":mnf1,
               "mnf1_out":mnf1_out,
               "mnf2":mnf2,
               "mnf2_out":mnf2_out,
               "mnf3":mnf3,
               "mnf4":mnf4,
               "mnf4_orig":mnf4_orig,
               "mnf5":mnf5,
               "mnf5_out":mnf5_out
               }
        


def render_edge_computing(idx):
    with st.expander("7. Edge Computing", expanded=True):
        k = f"ec_{idx}"
        
        ec1 = st.multiselect("EC-1. Como é que o edge computing está presente no produto que está a desenvolver ou testar?", [
            "Parte central da arquitetura do produto (ex.: edge gateway, controlador embebido)",
            "Utilizado para processamento local de dados ou analítica",
            "Utilizado para reduzir a latência em operações em tempo real",
            "Utilizado para reforçar a privacidade ou segurança ao processar localmente",
            "Utilizado para suportar inferência de IA ou decisão junto da máquina",
            "Outro"
        ], key=f"{k}_1")
        ec1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in ec1 else ""
        
        ec2 = st.radio("EC-2. Em que fase de desenvolvimento ou teste se encontra a funcionalidade de edge computing neste produto?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / operacional"
        ], key=f"{k}_2")
        
        ec3 = st.multiselect("EC-3. De que tipo de infraestrutura ou configuração edge depende este produto?", [
            "Microcontrolador embebido ou processador ao nível do dispositivo",
            "Edge gateway ou PC industrial junto do equipamento",
            "Servidor edge em instalações próprias (on-premise)",
            "Configuração híbrida (dispositivos edge ligados à nuvem)",
            "Outro"
        ], key=f"{k}_3")
        ec3_out = st.text_input("Especificar:", key=f"{k}_3o") if "Outro" in ec3 else ""
        
        ec4 = st.multiselect("EC-4. Quais são as principais funções ou vantagens alcançadas com edge computing neste produto?", [
            "Controlo ou automatização em tempo real (baixa latência)",
            "Analítica local ou monitorização de condição",
            "Filtragem ou pré-processamento de dados IoT antes de envio para a nuvem",
            "Operação offline ou continuidade quando há desconexão",
            "Garantia de confidencialidade / soberania dos dados",
            "Outro"
        ], key=f"{k}_4")
        ec4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in ec4 else ""
        
        ec5 = st.radio("EC-5. Como está o componente edge integrado com outros sistemas?", [
            "Sistema local autónomo (não ligado à nuvem)",
            "Ligado à nuvem para analítica agregada",
            "Ligado a sistemas de produção (MES/ERP/SCADA)",
            "Integrado com plataformas de dados de parceiros ou clientes",
            "Ainda não integrado (em teste)"
        ], key=f"{k}_5")
        
        return{
            "ec1":ec1,
            "ec1_out":ec1_out,
            "ec2":ec2,
            "ec3":ec3,
            "ec3_out":ec3_out,
            "ec4":ec4,
            "ec4_out":ec4_out,
            "ec5":ec5
            
            }
        


def render_ciberseguranca(idx):
    with st.expander("8. Cibersegurança", expanded=True):
        k = f"cs_{idx}"
        
        cs1 = st.multiselect("CS-1. Como é que a cibersegurança está presente no produto que está a desenvolver ou testar?", [
            "Funcionalidade central do produto (ex.: solução ou módulo de cibersegurança)",
            "Funcionalidade by design para proteger dados, redes ou equipamentos",
            "Aplicada para garantir trocas de dados seguras com parceiros ou sistemas na nuvem",
            "Utilizada para proteger componentes IoT/edge/IA integrados no produto",
            "Utilizada para salvaguardar o acesso do utilizador ou autenticação",
            "Outro"
        ], key=f"{k}_1")
        cs1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in cs1 else ""
        
        cs2 = st.radio("CS-2. Em que fase de desenvolvimento ou teste está a funcionalidade de cibersegurança?", [
            "Conceção / design (segurança por conceção em definição)",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / operacional"
        ], key=f"{k}_2")
        
        cs3 = st.multiselect("CS-3. Que aspetos do produto ou sistema estão protegidos através de cibersegurança?", [
            "Rede e conectividade (firewalls, segmentação, zero-trust)",
            "Armazenamento e transmissão de dados (encriptação, APIs seguras)",
            "Controlo de acesso e gestão de identidades (MFA, perfis por função)",
            "Controlo industrial / tecnologia operacional (proteção de PLC, SCADA)",
            "Interfaces de nuvem ou edge",
            "Integridade de software e firmware (assinatura de código, atualizações)",
            "Outro"
        ], key=f"{k}_3")
        cs3_out = st.text_input("Especificar:", key=f"{k}_3o") if "Outro" in cs3 else ""
        
        cs4 = st.multiselect("CS-4. Que frameworks ou práticas orientam a implementação de cibersegurança neste produto?", [
            "IEC 62443 (automação e controlo industrial)",
            "ISO 27001 / 27002 (gestão de segurança da informação)",
            "NIST Cybersecurity Framework",
            "Ato da Cibersegurança da UE ou regime de certificação de produtos",
            "Pen-testing / avaliação de vulnerabilidades realizada",
            "Nenhuma ainda / em desenvolvimento"
        ], key=f"{k}_4")
        
        return{
            "cs1":cs1,
            "cs1_out":cs1_out,
            "cs2":cs2,
            "cs3":cs3,
            "cs3_out":cs3_out,
            "cs4":cs4,
            }
        


def render_iot(idx):
    with st.expander("Internet das Coisas (IoT)", expanded=True):
        k = f"iot_{idx}"

        iot1 = st.multiselect(
            "IoT-1. Em que partes do produto/serviço são utilizadas soluções de Internet das Coisas?",
            [
                "Monitorização em tempo real do estado do produto/equipamento",
                "Recolha de dados de sensores (temperatura, vibração, consumo, etc.)",
                "Rastreio de localização (asset tracking, logística, frota)",
                "Controlo remoto ou automação de equipamentos",
                "Manutenção preditiva ou alertas automáticos",
                "Interação com o utilizador (ex.: aplicações móveis ligadas ao produto)",
                "Outro"
            ],
            key=f"{k}_1"
        )
        iot1_out = st.text_input(
            "Especificar outro:",
            key=f"{k}_1o"
        ) if "Outro" in iot1 else ""

        iot2 = st.radio(
            "IoT-2. Aproximadamente que percentagem das funcionalidades principais do produto depende de IoT?",
            [
                "0% (nenhuma funcionalidade depende de IoT)",
                "1–25%",
                "26–50%",
                "51–75%",
                "76–100% (quase todas as funcionalidades dependem de IoT)"
            ],
            key=f"{k}_2"
        )

        iot3 = st.radio(
            "IoT-3. Em termos de dados utilizados pelo produto, que proporção estima que seja gerada por dispositivos IoT (sensores, atuadores, equipamentos conectados)?",
            [
                "0% (não utiliza dados de IoT)",
                "1–25%",
                "26–50%",
                "51–75%",
                "76–100% (a maioria dos dados vem de IoT)"
            ],
            key=f"{k}_3"
        )

        iot4 = st.radio(
            "IoT-4. Quão crítica é a IoT para o funcionamento do produto?",
            [
                "Apenas complementar (o produto funcionaria praticamente igual sem IoT)",
                "Importante mas não crítica (algumas funcionalidades perder-se-iam)",
                "Crítica (o produto perderia grande parte da sua utilidade sem IoT)",
                "Essencial (o produto praticamente não existe sem IoT)"
            ],
            key=f"{k}_4"
        )

        iot5 = st.radio(
            "IoT-5. Em que fase de desenvolvimento ou implementação está a componente de IoT neste produto?",
            [
                "Fase de conceito / design",
                "Protótipo testado em laboratório",
                "Piloto em ambiente operacional",
                "Pré-série / implementação limitada",
                "Totalmente implementada em uso produtivo"
            ],
            key=f"{k}_5"
        )

        return {
            "iot1": iot1,
            "iot1_out": iot1_out,
            "iot2": iot2,
            "iot3": iot3,
            "iot4": iot4,
            "iot5": iot5
        }

# ========== END OF DIGITAL TECHNOLOGY FUNCTIONS ==========

def render_materiais_avancados(idx):
    with st.expander("9. Materiais Avançados", expanded=True):        
        k = f"ma_{idx}"
        
        ma1 = st.multiselect("MA-1. De que forma os materiais avançados estão presentes no produto que está a desenvolver ou testar?", [
            "Material nuclear do produto (estrutura principal ou camada funcional)",
            "Subcomponente (ex.: revestimento, interface, isolamento, selante)",
            "Utilizados para eficiência energética ou conceção leve (lightweight)",
            "Utilizados para durabilidade, resistência à corrosão ou ao desgaste",
            "Utilizados para reciclabilidade ou desempenho ambiental",
            "Outro"
        ], key=f"{k}_1")
        ma1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in ma1 else ""
        
        ma2 = st.multiselect("MA-2. Que tipos de materiais avançados estão integrados neste produto?", [
            "Materiais para eletrónica (semicondutores, polímeros condutores, sensores)",
            "Materiais energéticos (de mudança de fase, baterias, termoelétricos)",
            "Materiais para superfícies e interfaces (revestimentos, camadas de adesão, filmes finos)",
            "Materiais poliméricos e precursores (compósitos avançados, resinas, bioplásticos)",
           "Materiais estruturais e compósitos (ligas leves, cerâmicas, fibra de carbono)",
            "Materiais reciclados (matérias-primas secundárias ou polímeros/metais recuperados)",
            "Materiais de base biológica (biocompósitos, celulose, à base de lignina, etc.)",
            "Outro"
        ], key=f"{k}_2")
        ma2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in ma2 else ""
       
        ma3 = st.radio("MA-3. Em que fase de desenvolvimento ou teste estão estes materiais integrados no produto?", [
            "Conceito / formulação laboratorial",
            "Protótipo testado em condições controladas",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / em utilização comercial"
        ], key=f"{k}_3")
        
        ma4 = st.selectbox("MA-4. De onde provêm principalmente os materiais avançados deste produto?", [
            "",
            "Portugal",
            "Outro país da UE",
            "País europeu fora da UE",
            "EUA / América do Norte",
            "Ásia",
            "África / América do Sul",
            "Mistura de fornecedores da UE e de fora da UE",
            "Desenvolvidos internamente / com parceiro OIT"
            ], key=f"{k}_4")
        
        ma5 = st.multiselect("MA-5. Qual é a principal função dos materiais avançados neste produto?", [
            "Resistência, durabilidade ou resistência mecânica",
            "Gestão de energia ou térmica",
            "Desempenho elétrico ou ótico",
            "Redução de peso / melhoria de eficiência",
            "Redução do impacto ambiental",
            "Aumento da vida útil ou circularidade",
            "Outro"
        ], key=f"{k}_5")
        ma5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in ma5 else ""
    
    return{
        "ma1":ma1,
        "ma1_out":ma1_out,
        "ma2":ma2,
        "ma2_out":ma2_out,
        "ma3":ma3,
        "ma4":ma4,
        "ma5":ma5,
        "ma5_out":ma5_out
        }
        


def render_biotecnologia(idx):
     with st.expander("10. Aplicaçoes de Biotecnologia", expanded=True):
        k = f"bio_{idx}"
        
        bio1 = st.multiselect("BIO-1. Como está a biotecnologia presente no produto que está a desenvolver ou testar?", [
            "Elemento funcional central (ex.: material de base biológica ou produzido biologicamente)",
            "Utilizada para otimização de processo (fermentação, catálise enzimática, tratamento microbiano)",
            "Utilizada para geração ou conversão de bioenergia",
            "Utilizada para valorização de resíduos ou biorremediação",
            "Utilizada para substituir inputs sintéticos ou de origem fóssil",
            "Outro"
        ], key=f"{k}_1")
        bio1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in bio1 else ""
        
        bio2 = st.multiselect("BIO-2. Que tipo(s) de biotecnologia estão integrados neste produto?", [
            "Materiais de base biológica (biopolímeros, biocompósitos, fibras naturais, etc.)",
            "Bioenergia / biocombustíveis (biogás, bio-hidrogénio, conversão de biomassa)",
            "Biotecnologia ambiental (biorremediação, tratamento de águas residuais ou captura de CO₂ com microrganismos)",
            "Biotecnologia industrial (enzimas, fermentação, biocatálise)",
            "Produtos de base biológica (detergentes, lubrificantes, solventes, revestimentos, etc.)",
            "Outro"
        ], key=f"{k}_2")
        bio2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in bio2 else ""
        
        bio3 = st.radio("BIO-3. Em que fase de desenvolvimento ou teste está a biotecnologia aplicada neste produto?", [
            "Conceito / fase laboratorial",
            "Protótipo testado em laboratório ou planta piloto",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado / operacional"
        ], key=f"{k}_3")
        
        bio4 = st.selectbox("BIO-4. Qual a origem dos materiais biológicos, microrganismos ou componentes biotecnológicos?", [
            "",
            "Desenvolvidos internamente ou com parceiro OIT / investigação",
            "Fornecidos por fornecedor nacional (Portugal)",
            "Fornecidos por outro país da UE",
            "Fornecidos por país fora da UE",
            "Combinação de fontes internas e externas"
        ], key=f"{k}_4")
        
        bio5 = st.multiselect("BIO-5. Qual é a principal finalidade ou vantagem proporcionada pelo elemento biotecnológico deste produto?", [
            "Redução da pegada ambiental ou das emissões",
            "Melhoria da eficiência ou do yield do processo",
            "Substituição de substâncias perigosas / de base fóssil",
            "Criação de saídas renováveis ou biodegradáveis",
            "Recuperação ou conversão de energia a partir de resíduos",
            "Outro"
        ], key=f"{k}_5")
        bio5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in bio5 else ""
     
     return{
         "bio1":bio1,
         "bio1_out":bio1_out,
         "bio2":bio2,
         "bio2_out":bio2_out,
         "bio3":bio3,
         "bio4":bio4,
         "bio5":bio5,
         "bio5_out":bio5_out
         }
        


def render_reciclagem(idx):
      with st.expander("11. Soluçoes de Reciclagem", expanded=True):
        k = f"rcu_{idx}"
        
        rcu1 = st.multiselect("RCU-1. Como está a reciclagem presente no produto que está a desenvolver ou testar?", [
            "O produto é feito parcial ou totalmente com materiais reciclados",
            "O produto permite reciclagem ou recuperação de materiais após o uso",
            "O produto é concebido para reutilização, reparação ou remanufactura",
            "O produto integra subprodutos industriais reciclados ou matérias-primas secundárias",
            "O produto facilita a triagem, separação ou rastreabilidade de resíduos",
            "Outro"
        ], key=f"{k}_1")
        rcu1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in rcu1 else ""
        
        rcu2 = st.multiselect("RCU-2. Que tipo(s) de reciclagem ou utilização circular de materiais fazem parte deste produto?", [
            "Reciclagem de materiais – recuperação para reprocessamento (metais, plásticos, etc.)",
            "Circularidade e reutilização do produto – extensão da vida útil ou ciclos de reutilização",
            "Triagem e separação de resíduos – tecnologia ou design que permita a separação",
           "Simbiose industrial – oferta de resíduos a outra indústria como input",
            "Cadeias de retorno (reverse supply chains) – recolha de produtos ou componentes",
            "Utilização de inputs reciclados de outras indústrias",
            "Outro"
        ], key=f"{k}_2")
        rcu2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in rcu2 else ""
        
        rcu3 = st.radio("RCU-3. Em que fase de desenvolvimento ou teste estão integradas as práticas de reciclagem ou circularidade neste produto?", [
            "Conceito / design para reciclabilidade",
            "Protótipo usando materiais reciclados",
            "Piloto em ambiente de produção",
            "Pré-série / implementação limitada",
            "Totalmente implementado e operacional"
        ], key=f"{k}_3")
        
        rcu4 = st.selectbox("RCU-4. De onde provêm os materiais ou componentes reciclados utilizados neste produto?", [
            "",
            "Resíduos da produção interna (reciclagem interna)",
            "De outras empresas do consórcio",
            "De outras indústrias nacionais",
            "De fornecedores internacionais",
            "Mistura de várias fontes",
            "Sem input reciclado – foco na reciclabilidade no fim de vida"
        ], key=f"{k}_4")
       
        rcu5 = st.multiselect("RCU-5. Qual é o principal objetivo ou valor acrescentado do componente de reciclagem ou circularidade?", [
           "Redução do consumo de matérias-primas",
            "Redução de custos ou volumes de eliminação de resíduos",
            "Melhoria das credenciais de sustentabilidade do produto",
            "Reforço da rastreabilidade ou transparência de materiais",
            "Cumprimento de requisitos regulamentares ou de clientes",
            "Outro"
        ], key=f"{k}_5")
        rcu5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in rcu5 else ""
      return{
          "rcu1":rcu1,
          "rcu1_out":rcu1_out,
          "rcu2":rcu2,
          "rcu2_out":rcu2_out,
          "rcu3":rcu3,
          "rcu4":rcu4,
          "rcu5":rcu5,
          "rcu5_out":rcu5_out}
        


def render_poupanca_energia(idx):
      with st.expander("12. Tecnologias de Poupança de Energia", expanded=True):
        k = f"tpe_{idx}"
        
        tpe1 = st.multiselect("TPE-1. Como estão presentes as tecnologias de poupança de energia no produto que está a desenvolver ou testar?", [
           "Funcionalidade central do produto (ex.: equipamento ou sistema energeticamente eficiente)",
            "Funcionalidade integrada que melhora o desempenho energético de outro processo",
           "Componente de monitorização ou controlo para reduzir consumos",
            "Módulo de retrofit ou otimização para linhas de produção existentes",
            "Elemento de suporte em sistemas auxiliares (ex.: AVAC, iluminação, acionamentos)",
            "Outro"
           ], key=f"{k}_1")
        tpe1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in tpe1 else ""
        
        tpe2 = st.multiselect("TPE-2. Que tipo(s) de medidas de poupança de energia fazem parte deste produto?", [
            "Motores, acionamentos ou atuadores de alta eficiência",
            "Sistemas eficientes de aquecimento, arrefecimento ou secagem",
            "Recuperação de calor residual ou reaproveitamento de energia térmica",
            "Sensores inteligentes e controlo para otimização de processo",
            "Sistemas de gestão de energia ou demand-response",
            "Conceção energeticamente eficiente ou estruturas leves",
            "Outro"
        ], key=f"{k}_2")
        tpe2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in tpe2 else ""
        
        tpe3 = st.radio("TPE-3. Em que fase de desenvolvimento ou teste se encontra o componente de poupança de energia deste produto?", [
            "Fase de conceito / design",
            "Protótipo em condições laboratoriais",
            "Piloto testado em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado e operacional"
       ], key=f"{k}_3")
        
        tpe4 = st.multiselect("TPE-4. Em que parte do produto ou processo são aplicadas as tecnologias de poupança de energia?", [
           "Processo nuclear de fabrico ou transformação",
            "Sistemas auxiliares (aquecimento, arrefecimento, ar comprimido, etc.)",
           "Sistemas de gestão de edifícios ou instalações",
            "Transporte, logística ou movimentação de materiais",
            "Camada de controlo, automatização ou monitorização digital",
            "Outro"
        ], key=f"{k}_4")
        tpe4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in tpe4 else ""
       
        tpe5 = st.multiselect("TPE-5. Qual é o principal objetivo da integração de tecnologias de poupança de energia neste produto?", [
            "Reduzir o consumo total de energia",
            "Melhorar a estabilidade do processo ou o yield",
            "Diminuir CO₂ ou a pegada ambiental",
           "Reduzir custos operacionais",
            "Aumentar a autonomia ou flexibilidade do uso de energia",
            "Outro"
        ], key=f"{k}_5")
        tpe5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in tpe5 else ""
      
      return{
          "tpe1":tpe1,
          "tpe1_out":tpe1_out,
          "tpe2":tpe2,
          "tpe2_out":tpe2_out,
          "tpe3":tpe3,
          "tpe4":tpe4,
          "tpe4_out":tpe4_out,
          "tpe5":tpe5,
          "tpe5_out":tpe5_out
          }
  
        


def render_modelos_circulares(idx):
     with st.expander("13. Modelos de Negócio Industriais Circular", expanded=True):
          k = f"mnec_{idx}"
        
          mnec1 = st.multiselect("MNEC-1. Como é que o produto que está a desenvolver ou testar contribui para a economia circular?", [
            "O produto é concebido para durabilidade ou vida útil prolongada",
           "O produto pode ser desmontado, reparado ou remanufacturado",
            "O produto suporta modelos de partilha, leasing ou aluguer",
           "O produto facilita a reutilização ou revenda no fim de vida",
            "O produto permite cadeias de fornecimento circulares (ex.: fluxos de materiais secundários)",
            "O próprio produto integra um modelo baseado em serviços ou pay-per-use",
            "Outro"
            ], key=f"{k}_1")
          mnec1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in mnec1 else ""
        
          mnec2 = st.multiselect("MNEC-2. Que modelo(s) específico(s) de economia circular estão associados a este produto?", [
           "Remanufactura – recuperação de componentes para reutilização em novos produtos",
           "Serviços de reparação e manutenção – extensão da vida útil",
            "Aluguer, leasing ou modelos baseados em desempenho",
           "Revenda / reutilização – segunda vida ou recondicionamento",
            "Design circular – produtos concebidos para fácil desmontagem e reciclagem",
            "Design para durabilidade – vida operacional mais longa",
            "Integração de ciclos de materiais – uso de matérias-primas secundárias",
            "Outro"
          ], key=f"{k}_2")
          mnec2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in mnec2 else ""
        
          mnec3 = st.radio("MNEC-3. Em que fase de desenvolvimento ou teste está o modelo de negócio circular associado a este produto?", [
           "Fase de conceito / design",
            "Protótipo testado em laboratório ou linha piloto",
            "Piloto ou demonstração com clientes",
            "Pré-série / implementação limitada",
            "Totalmente implementado e operacional"
        ], key=f"{k}_3")
        
          mnec4 = st.multiselect("MNEC-4. Quem participa na implementação do modelo circular para este produto?", [
            "Apenas operações internas",
            "Fornecedores ou fabricantes de componentes",
            "Clientes / utilizadores (ex.: take-back ou leasing)",
            "Parceiros industriais ou redes de simbiose",
            "Stakeholders locais ou regionais (cadeias curtas)",
           "Parceiros de investigação ou certificação",
            "Outro"
           ], key=f"{k}_4")
          mnec4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in mnec4 else ""
        
          mnec5 = st.multiselect("MNEC-5. Qual é o principal objetivo ou valor criado pela aplicação deste modelo circular?", [
            "Reduzir resíduos ou uso de materiais",
            "Prolongar a vida útil ou a taxa de utilização do produto",
            "Reduzir custos de produção ou operação",
           "Reforçar a fidelização do cliente ou a diferenciação de serviço",
            "Criar novas fontes de receita (serviços, remanufactura, revenda)",
            "Reduzir a pegada de carbono ou ambiental",
            "Outro"
           ], key=f"{k}_5")
          mnec5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in mnec5 else ""
     
     return{
         "mnec1":mnec1,
         "mnec1_out":mnec1_out,
         "mnec2":mnec2,
         "mnec2_out":mnec2_out,
         "mnec3":mnec3,
         "mnec4":mnec4,
         "mnec4_out":mnec4_out,
         "mnec5":mnec5,
         "mnec5_out":mnec5_out
         }
        


def render_producao_limpa(idx):
       with st.expander("14. Tecnologias de Produção Limpa", expanded=True):
           k = f"tpl_{idx}"
        
           tpl1 = st.multiselect("TPL-1. Como estão presentes as tecnologias de produção limpa no produto que está a desenvolver ou testar?", [
            "Funcionalidade central do produto (ex.: processo/equipamento de baixas emissões ou baixo desperdício)",
           "Funcionalidade integrada que reduz impactos ambientais durante a produção",
           "Módulo de otimização de processo que melhora a eficiência de materiais ou energia",
            "Tecnologia que previne ou trata emissões, descargas ou resíduos",
            "Substituição de inputs perigosos ou poluentes",
            "Outro"
          ], key=f"{k}_1")
           tpl1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in tpl1 else ""
        
           tpl2 = st.multiselect("TPL-2. Que tecnologias específicas de produção limpa estão integradas neste produto?", [
           "Prevenção da poluição ou conceção de processos mais limpos",
           "Sistemas de produção em circuito fechado ou sem descarga",
            "Sistemas de poupança de água ou reciclagem de águas residuais",
            "Tecnologias de redução ou filtração de emissões atmosféricas",
            "Processos químicos mais limpos ou formulações isentas de solventes",
            "Minimização ou recuperação de resíduos no próprio processo",
            "Substituição ou redução de materiais perigosos",
           "Outro"
           ], key=f"{k}_2")
           tpl2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in tpl2 else ""
        
           tpl3 = st.radio("TPL-3. Em que fase de desenvolvimento ou teste se encontra a tecnologia de produção limpa neste produto?", [
           "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado e operacional"
           ], key=f"{k}_3")
        
           tpl4 = st.multiselect("TPL-4. Que áreas ou operações de produção são visadas por esta tecnologia?", [
            "Processo nuclear de fabrico",
            "Processos auxiliares (ex.: arrefecimento, limpeza, manutenção)",
            "Etapa de tratamento ou recuperação de resíduos",
            "Preparação ou pré-tratamento de matérias-primas",
           "Embalagem ou logística",
            "Outro"
        ], key=f"{k}_4")
           tpl4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in tpl4 else ""
        
           tpl5 = st.multiselect("TPL-5. Qual é a principal finalidade ou benefício alcançado com esta tecnologia de produção limpa?", [
            "Redução de emissões ou descargas poluentes",
           "Redução na geração de resíduos",
            "Redução do consumo de energia ou água",
            "Substituição de substâncias perigosas",
            "Melhoria da segurança do produto ou do trabalhador",
           "Conformidade com regulamentos ou certificações ambientais",
            "Outro"
        ], key=f"{k}_5")
           tpl5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in tpl5 else ""
       
       return{
           "tpl1":tpl1,
           "tpl1_out":tpl1_out,
           "tpl2":tpl2,
           "tpl2_out":tpl2_out,
           "tpl3":tpl3,
           "tpl4":tpl4,
           "tpl4_out":tpl4_out,
           "tpl5":tpl5,
           "tpl5_out":tpl5_out
           }
        


def render_captura_carbono(idx):
       with st.expander("15. Tecnologias de Captura ou Redução de Carbono (CO₂)", expanded=True):
          k = f"tcc_{idx}"
        
          tcc1 = st.multiselect("TCC-1. Como está presente a captura de carbono ou a redução de CO₂ no produto que está a desenvolver ou testar?", [
            "Funcionalidade central (produto concebido para capturar ou armazenar CO₂)",
            "Processo ou sistema que reduz emissões diretas durante a produção",
            "Tecnologia que aumenta a eficiência energética ou reduz o uso de combustíveis fósseis",
           "Componente que viabiliza inputs de baixo carbono ou substitui materiais com menor carbono incorporado",
            "Sistema digital ou de monitorização que apoia o controlo e otimização de emissões",
           "Outro"
        ], key=f"{k}_1")
          tcc1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in tcc1 else ""
        
          tcc2 = st.multiselect("TCC-2. Que tipo(s) específicos de abordagem de captura ou redução de carbono estão integrados neste produto?", [
            "Captura pós-combustão – separação de CO₂ de gases de chaminé/processo",
            "Captura pré-combustão – remoção de CO₂ antes da combustão do combustível",
            "Captura direta do ar – captura de CO₂ diretamente do ar ambiente",
            "Otimização de processo – redução de CO₂ via eficiência ou controlo",
            "Substituição de materiais – substituição de materiais ou combustíveis intensivos em carbono",
            "Utilização / valorização de CO₂ – conversão do CO₂ capturado em produtos úteis",
            "Outro"
        ], key=f"{k}_2")
          tcc2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in tcc2 else ""
        
          tcc3 = st.radio("TCC-3. Em que fase de desenvolvimento ou teste está a tecnologia de redução ou captura de CO₂ neste produto?", [
            "Conceito / testes laboratoriais",
            "Protótipo em laboratório ou planta piloto",
            "Piloto testado em ambiente industrial",
            "Pré-série / implementação limitada",
           "Totalmente implementado e operacional"
        ], key=f"{k}_3")
        
          tcc4 = st.multiselect("TCC-4. Qual é a principal fonte ou processo visado para captura ou redução de CO₂?", [
            "Emissões de processo (combustão ou reações químicas)",
           "Uso de energia ou combustão de combustíveis",
            "Inputs e matérias-primas industriais",
            "Transporte ou logística",
            "Fase de utilização do produto",
            "Tratamento de fim de vida ou reciclagem",
            "Outro"
        ], key=f"{k}_4")
          tcc4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in tcc4 else ""
        
          tcc5 = st.multiselect("TCC-5. Qual é a principal finalidade ou benefício esperado da integração de funcionalidades de redução ou captura de CO₂ neste produto?", [
            "Redução de emissões de gases com efeito de estufa",
            "Cumprimento de regulamentos ambientais",
            "Melhoria da eficiência energética e menores custos de combustível",
            "Criação de produtos ou serviços low-carbon com valor de mercado",
            "Melhoria da reputação de marca ou resposta à procura por soluções de baixo carbono",
            "Outro"
        ], key=f"{k}_5")
          tcc5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in tcc5 else ""
       
       return{
           "tcc1":tcc1,
           "tcc1_out":tcc1_out,
           "tcc2":tcc2,
           "tcc2_out":tcc2_out,
           "tcc3":tcc3,
           "tcc4":tcc4,
           "tcc4_out":tcc4_out,
           "tcc5":tcc5,
           "tcc5_out":tcc5_out
               }
        


def render_energias_renovaveis(idx):
       with st.expander("16. Integração de Energias Renováveis", expanded=True):
           k = f"ier_{idx}"
        
           ier1 = st.multiselect("IER-1. Como estão presentes as energias renováveis no produto que está a desenvolver ou testar?", [
            "O produto gera energia renovável (ex.: sistema solar, eólico, bioenergia)",
            "O produto possibilita o uso de energia renovável em processos industriais",
            "O produto armazena ou gere energia renovável (ex.: baterias, armazenamento térmico)",
            "O produto controla ou otimiza fluxos de energia renovável",
            "O produto facilita a integração de renováveis em infraestruturas existentes (ex.: sistemas híbridos, smart grids)",
            "Outro"
           ], key=f"{k}_1")
           ier1_out = st.text_input("Especificar:", key=f"{k}_1o") if "Outro" in ier1 else ""
        
           ier2 = st.multiselect("IER-2. Que fonte(s) de energia renovável estão associadas a este produto?", [
               "Solar (térmica ou fotovoltaica)",
            "Eólica",
            "Biomassa / bioenergia",
            "Geotérmica",
            "Hídrica ou marinha",
            "Híbrida (múltiplas fontes renováveis)",
            "Outro"
           ], key=f"{k}_2")
           ier2_out = st.text_input("Especificar:", key=f"{k}_2o") if "Outro" in ier2 else ""
        
           ier3 = st.radio("IER-3. Em que fase de desenvolvimento ou teste está a integração de energias renováveis neste produto?", [
            "Fase de conceito / design",
            "Protótipo testado em laboratório",
            "Piloto em ambiente operacional",
            "Pré-série / implementação limitada",
            "Totalmente implementado e operacional"
        ], key=f"{k}_3")
        
           ier4 = st.multiselect("IER-4. Qual é o principal objetivo ou função da integração de energias renováveis neste produto?", [
            "Reduzir o consumo ou a dependência de energia fóssil",
            "Alcançar autonomia energética ou autoconsumo",
            "Reduzir emissões de gases com efeito de estufa",
            "Reduzir custos operacionais",
            "Melhorar a resiliência face à volatilidade de preços de energia",
            "Cumprir requisitos ambientais ou de clientes",
            "Outro"
        ], key=f"{k}_4")
           ier4_out = st.text_input("Especificar:", key=f"{k}_4o") if "Outro" in ier4 else ""
        
           ier5 = st.multiselect("IER-5. Onde é integrada a energia renovável no produto ou sistema?", [
             "Fornecimento energético do processo nuclear",
            "Sistemas auxiliares (aquecimento, arrefecimento, ventilação, iluminação)",
            "Sistemas de carregamento ou armazenamento",
            "Operações da cadeia de fornecimento ou logística",
            "Infraestrutura ao nível do edifício ou do local",
            "Outro"
           ], key=f"{k}_5")
           ier5_out = st.text_input("Especificar:", key=f"{k}_5o") if "Outro" in ier5 else ""
       
       return{
           "ier1":ier1,
           "ier1_out":ier1_out,
           "ier2":ier2,
           "ier2_out":ier2_out,
           "ier3":ier3,
           "ier4":ier4,
           "ier4_out":ier4_out,
           "ier5":ier5,
           "ier5_out":ier5_out
           }
        

# Main detail rendering function
def render_tech_details():
    idx = st.session_state.current_product_index
    data = st.session_state.responses[idx]
    
    # Get PPS info
    pps_info = data.get('pps_info', {})
    
    st.title(f"Produto {idx + 1} de {st.session_state.n_products}")
    st.header("Perguntas Detalhadas sobre as Tecnologias")
    
    # Display in an info box like in section 2
    st.markdown(f"""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3; margin-bottom: 20px;">
        <p style="margin: 5px 0;"><strong>Work Package:</strong> {data.get('work_project', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>PPS:</strong> {pps_info.get('pps_num', 'N/A')}</p>
        <p style="margin: 5px 0;"><strong>Designação:</strong> {pps_info.get('designation', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    tech_map_digital = {
     "Computação em Nuvem (Cloud Computing)": render_computacao_nuvem,
     "Robótica": render_robotica,
     "Inteligência Artificial e Big Data": render_ia_bigdata,
     "Internet das Coisas (IoT)": render_iot,
     "Realidade Aumentada / Realidade Virtual (RA/RV)": render_ra_rv,
     "Blockchain": render_blockchain,
     "Micro / Nanoeletrónica e Fotónica": render_micro_nano,
     "Edge Computing": render_edge_computing,
     "Cibersegurança": render_ciberseguranca,
     # "Outra Inovação Digital" não tem (ainda) bloco detalhado próprio
 }

    
    tech_map_ambiental = {
    "Materiais Avançados": render_materiais_avancados,
    "Aplicações de Biotecnologia": render_biotecnologia,
    "Soluções de Reciclagem": render_reciclagem,
    "Tecnologias de Poupança de Energia": render_poupanca_energia,
    "Modelos de Negócio Industriais Circulares": render_modelos_circulares,
    "Tecnologias de Produção Limpa": render_producao_limpa,
    "Tecnologias de Captura ou Redução de Carbono (CO₂)": render_captura_carbono,
    "Integração de Energias Renováveis": render_energias_renovaveis,
    # "Outra Inovação Ambiental" também não tem bloco detalhado próprio por agora
}

    
    # Render digital technologies
    if data.get("tech_digitais"):
        st.subheader(" Tecnologias Digitais")
        for tech in data.get("tech_digitais", []):
            if tech in tech_map_digital:
                result = tech_map_digital[tech](idx)
                if "detalhes_tech" not in data:
                    data["detalhes_tech"] = {}
                data["detalhes_tech"][tech] = result
    
    # Render environmental technologies
    if data.get("tech_ambientais"):
        st.subheader(" Tecnologias Ambientais")
        for tech in data.get("tech_ambientais", []):
            if tech in tech_map_ambiental:
                result = tech_map_ambiental[tech](idx)
                if "detalhes_tech" not in data:
                    data["detalhes_tech"] = {}
                data["detalhes_tech"][tech] = result
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Anterior", key="prev_details"):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("Próximo", key="next_details"):
            st.session_state.responses[idx] = data
            if idx < st.session_state.n_products - 1:
                st.session_state.current_product_index += 1
                st.session_state.step = 1
                st.rerun()
            else:
                st.session_state.step = 3
                st.rerun()

# Final summary
def render_summary():
    st.title("Resumo e Submissão")
    st.header("Obrigado pela sua participação!")
    st.subheader("Informações da Empresa")
    company = st.session_state.company
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Número de Trabalhadores:** {company['num_trabalhadores']}")
        st.write(f"**Região:** {company['regiao']}")
    with col2:
        # FIX: Handle both list and string for tipo_organizacao
        tipo_org = company['tipo_organizacao'] if isinstance(company['tipo_organizacao'], str) else ', '.join(company['tipo_organizacao'])
        st.write(f"**Tipo de Organização:** {tipo_org}")
        st.write(f"**Número de PPS:** {company['num_pps']}")
    st.subheader("Resumo dos Produtos")
    products_summary = []
    for i, resp in enumerate(st.session_state.responses):
        # Get PPS info to show number and designation
        pps_info = resp.get('pps_info', {})
        pps_num = pps_info.get('pps_num', 'N/A')
        pps_name = pps_info.get('designation', 'N/A')
        tech_dig_str = ', '.join(resp.get('tech_digitais', [])) if resp.get('tech_digitais') else 'Nenhuma'
        tech_amb_str = ', '.join(resp.get('tech_ambientais', [])) if resp.get('tech_ambientais') else 'Nenhuma'
        products_summary.append({
            'PPS Nº': pps_num,
            'Designação': pps_name[:60] + '...' if len(pps_name) > 60 else pps_name,
            'Work Package': resp.get('work_project', 'N/A'),
            'Tecnologias Digitais': tech_dig_str,
            'Tecnologias Ambientais': tech_amb_str
        })
    st.table(pd.DataFrame(products_summary))
    if st.button("Submeter Respostas", key="submit_final"):
        # Save data in improved format (two files)
        main_file, detail_file, company_id = save_survey_data_improved(
            company=st.session_state.company,
            responses=st.session_state.responses,
            pps_data=PPS_DATA
        )
        st.success("✅ Respostas submetidas com sucesso!")
        # Provide download buttons for both files
 
# Main app
def main():
    st.markdown("""
        <style>
        /* Base responsive styling */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        /* Button styling - mobile-first approach */
        .stButton > button {
            width: 100%;
            height: 48px; /* Touch-friendly height */
            font-size: 16px; /* Prevents zoom on iOS */
            border-radius: 8px;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        /* Expander styling for better mobile experience */
        div[data-testid="stExpander"] {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 1rem;
            background-color: #fafafa;
        }
        
        /* Input field improvements for mobile */
        .stSelectbox > div > div {
            font-size: 16px; /* Prevents zoom on iOS */
        }
        
        .stTextInput > div > div > input {
            font-size: 16px; /* Prevents zoom on iOS */
            padding: 12px;
        }
        
        .stNumberInput > div > div > input {
            font-size: 16px;
            padding: 12px;
        }
        
        /* Radio button improvements */
        .stRadio > label {
            font-size: 16px;
            line-height: 1.4;
        }
        
        /* Multiselect improvements */
        .stMultiSelect > label {
            font-size: 16px;
            line-height: 1.4;
        }
        
        /* Column spacing for mobile */
        .row-widget.stHorizontal {
            gap: 1rem;
        }
        
        /* Table responsiveness */
        .dataframe {
            font-size: 14px;
            overflow-x: auto;
        }
        
        /* Headers for better mobile readability */
        h1 {
            font-size: 1.5rem;
            line-height: 1.3;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 1.3rem;
            line-height: 1.3;
            margin-bottom: 0.8rem;
        }
        
        h3 {
            font-size: 1.1rem;
            line-height: 1.3;
            margin-bottom: 0.6rem;
        }
        
        /* Desktop-specific improvements */
        @media (min-width: 768px) {
            .main .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .stButton > button {
                width: auto;
                min-width: 120px;
                padding: 0.5rem 1.5rem;
            }
            
            /* Better column layout on desktop */
            .row-widget.stHorizontal {
                gap: 2rem;
            }
            
            /* Larger headers on desktop */
            h1 {
                font-size: 2rem;
            }
            
            h2 {
                font-size: 1.5rem;
            }
            
            h3 {
                font-size: 1.2rem;
            }
        }
        
        /* Large desktop screens */
        @media (min-width: 1200px) {
            .main .block-container {
                max-width: 1400px;
            }
        }
        
        /* Focus states for accessibility */
        .stButton > button:focus {
            outline: 2px solid #0066cc;
            outline-offset: 2px;
        }
        
        /* Loading state improvements */
        .stSpinner {
            text-align: center;
            margin: 2rem 0;
        }
        
        /* Error/success message styling */
        .stAlert {
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Hide Streamlit menu and footer on mobile for cleaner look */
        @media (max-width: 768px) {
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        }
        
        /* Improve form spacing */
        .stForm {
            padding: 1rem;
            border-radius: 8px;
            background-color: #f8f9fa;
            margin-bottom: 1rem;
        }
        
        /* Better select slider for mobile */
        .stSelectSlider {
            margin: 1rem 0;
        }
        
        .stSelectSlider > div > div {
            font-size: 14px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.step == 0:
        render_section_1()
    elif st.session_state.step == 1:
        render_section_2_intro()
    elif st.session_state.step == 2:
        render_tech_details()
    elif st.session_state.step == 3:
        render_summary()

if __name__ == "__main__":
    main()
       
        
        
        
        
        
