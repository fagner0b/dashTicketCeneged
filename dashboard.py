import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard Tickets Ceneged - Neoenergia",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def filter_team_technicians(df):
    """Filtra apenas tickets do time principal"""
    main_technicians = ['Anthony Valdemar Lopes da Silva', 'Jéssica Bernardo', 'Thiago Augusto Silva Martins', 'Fagner Brito']
    tech_column = 'Atribuído - Técnico'
    
    if tech_column not in df.columns:
        return df
    
    # Limpa dados de técnico
    df = df.copy()
    df[tech_column] = df[tech_column].astype(str).str.strip().str.replace('"', '')
    
    # Função para verificar se todos os técnicos são do time principal
    def is_team_ticket(tech_string):
        if pd.isna(tech_string) or tech_string == '' or tech_string == 'nan':
            return False
        
        # Divide pelos separadores possíveis
        technicians = []
        for separator in ['<br>', ' <br>', '<br> ', ' <br> ']:
            if separator in tech_string:
                technicians = [t.strip() for t in tech_string.split(separator) if t.strip()]
                break
        else:
            technicians = [tech_string.strip()]
        
        # Verifica se todos os técnicos estão no time principal
        return all(tech in main_technicians for tech in technicians if tech)
    
    # Aplica filtro
    team_mask = df[tech_column].apply(is_team_ticket)
    return df[team_mask]

@st.cache_data
def load_data(uploaded_file=None):
    """Carrega e processa os dados do CSV"""
    try:
        if uploaded_file is not None:
            # Tenta diferentes separadores e encodings para arquivo carregado
            separators = [';', ',', '\t']
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            df = None
            for sep in separators:
                for enc in encodings:
                    try:
                        uploaded_file.seek(0)  # Reset file pointer
                        df = pd.read_csv(uploaded_file, sep=sep, encoding=enc)
                        # Verifica se o CSV foi lido corretamente
                        if len(df.columns) > 1 and len(df) > 0:
                            st.info(f"✅ Arquivo carregado com sucesso! Separador: '{sep}', Encoding: {enc}")
                            break
                    except Exception:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            
            if df is None or len(df.columns) <= 1:
                raise ValueError("Não foi possível detectar o formato correto do arquivo CSV")
        else:
            # Carrega arquivo padrão
            df = pd.read_csv('glpi.csv', sep=';', encoding='utf-8')
        
        # Limpa nomes das colunas
        df.columns = df.columns.str.strip().str.replace('"', '')
        
        # Converte datas
        date_columns = ['Data de abertura', 'Última atualização']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d-%m-%Y %H:%M', errors='coerce')
        
        # Limpa dados textuais
        text_columns = ['Status', 'Prioridade', 'Localização', 'Plug-ins - Departamento - Departamento']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.replace('"', '')
        
        # Aplica filtro do time GLOBALMENTE
        df = filter_team_technicians(df)
        
        return df
    except Exception as e:
        error_msg = str(e)
        if "No columns to parse from file" in error_msg:
            st.error("❌ **Erro no formato do arquivo CSV:**")
            st.error("• Verifique se o arquivo contém dados válidos")
            st.error("• Certifique-se que o arquivo tem cabeçalhos nas colunas")
            st.error("• Experimente salvar o arquivo com encoding UTF-8")
            st.error("• Formatos aceitos: separados por ';', ',' ou tab")
        else:
            st.error(f"❌ **Erro ao carregar dados:** {error_msg}")
        
        # Exibe informações adicionais sobre o arquivo
        if uploaded_file is not None:
            st.info(f"📄 **Arquivo enviado:** {uploaded_file.name}")
            st.info(f"📊 **Tamanho:** {uploaded_file.size} bytes")
        
        return None



def create_monthly_timeline_chart(df, estado_filter=None):
    """Cria gráfico de evolução mensal dos tickets"""
    df_timeline = df.copy()
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = preprocess_sla_data(df_timeline)
        df_timeline = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    df_timeline = df_timeline.dropna(subset=['Data de abertura'])
    
    # Cria coluna de ano-mês
    df_timeline['Ano_Mes'] = df_timeline['Data de abertura'].dt.to_period('M')
    
    # Conta tickets por mês
    monthly_counts = df_timeline.groupby('Ano_Mes').size().reset_index(name='Quantidade')
    monthly_counts['Mes_Ano'] = monthly_counts['Ano_Mes'].astype(str)
    
    fig = px.line(
        monthly_counts,
        x='Mes_Ano',
        y='Quantidade',
        title="Evolução Mensal de Tickets Criados",
        labels={'Mes_Ano': 'Mês/Ano', 'Quantidade': 'Número de Tickets'},
        markers=True
    )
    
    fig.update_traces(mode='lines+markers+text', textposition='top center', texttemplate='%{y}')
    fig.update_layout(height=400, xaxis_tickangle=-45)
    
    return fig

def create_department_chart(df, estado_filter=None, month_filter=None):
    """Cria gráfico de tickets por departamento"""
    df_filtered = df.copy()
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = preprocess_sla_data(df_filtered)
        df_filtered = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês se especificado
    if month_filter and len(month_filter) > 0:
        if 'Ano_Mes' not in df_filtered.columns:
            df_filtered = preprocess_sla_data(df_filtered)
        df_filtered = df_filtered[df_filtered['Ano_Mes'].astype(str).isin(month_filter)]
    
    dept_counts = df_filtered['Plug-ins - Departamento - Departamento'].value_counts().head(10)
    
    fig = px.bar(
        x=dept_counts.values,
        y=dept_counts.index,
        orientation='h',
        title="Top 10 Departamentos com Mais Tickets",
        labels={'x': 'Quantidade de Tickets', 'y': 'Departamento'}
    )
    
    fig.update_layout(height=500)
    
    return fig

def create_location_chart(df, estado_filter=None, month_filter=None):
    """Cria gráfico de tickets por localização"""
    df_filtered = df.copy()
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = preprocess_sla_data(df_filtered)
        df_filtered = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês se especificado
    if month_filter and len(month_filter) > 0:
        if 'Ano_Mes' not in df_filtered.columns:
            df_filtered = preprocess_sla_data(df_filtered)
        df_filtered = df_filtered[df_filtered['Ano_Mes'].astype(str).isin(month_filter)]
    
    location_counts = df_filtered['Localização'].value_counts().head(15)
    
    fig = px.bar(
        x=location_counts.index,
        y=location_counts.values,
        title="Tickets por Localização (Top 15)",
        labels={'x': 'Localização', 'y': 'Quantidade de Tickets'}
    )
    
    fig.update_layout(height=400, xaxis_tickangle=-45)
    
    return fig

def preprocess_sla_data(df):
    """Pré-processa dados de SLA"""
    df_sla = df.copy()
    
    # Define categorias
    df_sla['Categoria_SLA'] = 'Outros'
    df_sla.loc[df_sla['Categoria'].str.contains('TI - Infra', na=False), 'Categoria_SLA'] = 'TI Infra'
    df_sla.loc[df_sla['Categoria'].str.contains('TI - Sistemas > GPM', na=False), 'Categoria_SLA'] = 'TI Sistema GPM'
    df_sla.loc[df_sla['Categoria'].str.contains('TI - Infra > Telefonia', na=False), 'Categoria_SLA'] = 'TI Sistema Telefonia'
    
    # Converte coluna de excesso para booleano
    df_sla['SLA_Excedido'] = df_sla['Tempo para resolver excedido'].str.strip().str.replace('"', '') == 'Sim'
    
    # Cria coluna de mês/ano
    df_sla = df_sla.dropna(subset=['Data de abertura'])
    df_sla['Ano_Mes'] = df_sla['Data de abertura'].dt.to_period('M')
    
    # Adiciona filtro de entidade
    df_sla['Estado'] = 'Outros'
    
    # Limpa a coluna Entidade primeiro
    entidade_clean = df_sla['Entidade'].str.strip().str.replace('"', '')
    
    # PE: Contém "Ticket > TI > Cng PE" mas NÃO contém "Cng RN"
    pe_mask = entidade_clean.str.contains('Ticket > TI > Cng PE', na=False) & ~entidade_clean.str.contains('Cng RN', na=False)
    df_sla.loc[pe_mask, 'Estado'] = 'PE'
    
    # RN: Contém "Ticket > TI > Cng PE > Cng RN"
    rn_mask = entidade_clean.str.contains('Ticket > TI > Cng PE > Cng RN', na=False)
    df_sla.loc[rn_mask, 'Estado'] = 'RN'
    
    return df_sla

def create_sla_compliance_chart(df, estado_filter=None, month_filter=None):
    """Cria gráfico de compliance SLA por mês e categoria"""
    df_sla = preprocess_sla_data(df)
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês se especificado
    if month_filter and len(month_filter) > 0:
        df_sla = df_sla[df_sla['Ano_Mes'].astype(str).isin(month_filter)]
    
    # Filtra apenas as categorias principais
    df_filtered = df_sla[df_sla['Categoria_SLA'].isin(['TI Infra', 'TI Sistema GPM', 'TI Sistema Telefonia'])]
    
    # Agrupa por mês, categoria e status SLA
    sla_summary = df_filtered.groupby(['Ano_Mes', 'Categoria_SLA', 'SLA_Excedido']).size().reset_index(name='Quantidade')
    sla_summary['Mes_Ano'] = sla_summary['Ano_Mes'].astype(str)
    sla_summary['Status_SLA'] = sla_summary['SLA_Excedido'].map({True: 'Fora do Prazo', False: 'Dentro do Prazo'})
    
    fig = px.bar(
        sla_summary,
        x='Mes_Ano',
        y='Quantidade',
        color='Status_SLA',
        facet_col='Categoria_SLA',
        title="Compliance SLA por Mês e Categoria",
        labels={'Mes_Ano': 'Mês/Ano', 'Quantidade': 'Número de Tickets'},
        color_discrete_map={'Dentro do Prazo': '#28a745', 'Fora do Prazo': '#dc3545'}
    )
    
    fig.update_layout(height=500, xaxis_tickangle=-45)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    return fig

def create_sla_summary_chart(df, estado_filter=None):
    """Cria gráfico consolidado de SLA"""
    df_sla = preprocess_sla_data(df)
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Agrupa todas as categorias
    categories = ['TI Infra', 'TI Sistema GPM', 'TI Sistema Telefonia', 'Total']
    summary_data = []
    
    for cat in categories[:-1]:  # Todas exceto Total
        cat_data = df_sla[df_sla['Categoria_SLA'] == cat]
        total = len(cat_data)
        dentro_prazo = len(cat_data[~cat_data['SLA_Excedido']])
        fora_prazo = len(cat_data[cat_data['SLA_Excedido']])
        
        if total > 0:  # Só adiciona se tiver dados
            summary_data.extend([
                {'Categoria': cat, 'Status': 'Dentro do Prazo', 'Quantidade': dentro_prazo},
                {'Categoria': cat, 'Status': 'Fora do Prazo', 'Quantidade': fora_prazo}
            ])
    
    # Total (todas categorias principais)
    all_data = df_sla[df_sla['Categoria_SLA'].isin(['TI Infra', 'TI Sistema GPM', 'TI Sistema Telefonia'])]
    total_dentro = len(all_data[~all_data['SLA_Excedido']])
    total_fora = len(all_data[all_data['SLA_Excedido']])
    
    summary_data.extend([
        {'Categoria': 'Total', 'Status': 'Dentro do Prazo', 'Quantidade': total_dentro},
        {'Categoria': 'Total', 'Status': 'Fora do Prazo', 'Quantidade': total_fora}
    ])
    
    summary_df = pd.DataFrame(summary_data)
    
    fig = px.bar(
        summary_df,
        x='Categoria',
        y='Quantidade',
        color='Status',
        title="Resumo Compliance SLA por Categoria",
        labels={'Categoria': 'Categoria', 'Quantidade': 'Número de Tickets'},
        color_discrete_map={'Dentro do Prazo': '#28a745', 'Fora do Prazo': '#dc3545'},
        text='Quantidade'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400)
    
    return fig

def create_technician_chart(df, estado_filter=None, month_filter=None):
    """Cria gráfico de tickets por técnico (time principal)"""
    tech_column = 'Atribuído - Técnico'
    
    if tech_column not in df.columns:
        return None
    
    df_filtered = df.copy()
    
    # Aplica filtro de estado se especificado
    if estado_filter and len(estado_filter) > 0:
        df_sla = preprocess_sla_data(df_filtered)
        df_filtered = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês se especificado
    if month_filter and len(month_filter) > 0:
        if 'Ano_Mes' not in df_filtered.columns:
            df_filtered = preprocess_sla_data(df_filtered)
        df_filtered = df_filtered[df_filtered['Ano_Mes'].astype(str).isin(month_filter)]
    
    # Expande técnicos múltiplos para contar individualmente
    tech_data = []
    for _, row in df_filtered.iterrows():
        tech_string = str(row[tech_column]).strip().replace('"', '')
        
        if tech_string == '' or tech_string == 'nan':
            continue
            
        # Divide pelos separadores possíveis
        technicians = []
        for separator in ['<br>', ' <br>', '<br> ', ' <br> ']:
            if separator in tech_string:
                technicians = [t.strip() for t in tech_string.split(separator) if t.strip()]
                break
        else:
            technicians = [tech_string.strip()]
        
        # Adiciona cada técnico individualmente
        for tech in technicians:
            if tech:
                tech_data.append(tech)
    
    if not tech_data:
        return None
    
    tech_series = pd.Series(tech_data)
    tech_counts = tech_series.value_counts()
    
    # Gráfico de pizza
    fig = px.pie(
        values=tech_counts.values,
        names=tech_counts.index,
        title="Distribuição de Tickets por Técnico"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

# Interface Principal
def main():
    st.title("🎫 Ticket Ceneged - Neoenergia")
    st.markdown("---")
    
    # Sidebar para upload de arquivo e filtros
    with st.sidebar:
        # Logo
        try:
            # Tenta diferentes configurações para melhor qualidade
            st.image(
                "Logo-Ceneged-Branco.png", 
                width=250
            )
            st.markdown("---")
        except:
            pass  # Se não encontrar o logo, continua sem ele
        
        st.header("📁 Carregamento de Dados")
        uploaded_file = st.file_uploader(
            "Escolha um arquivo CSV",
            type=['csv'],
            help="Upload do arquivo GLPI CSV para atualizar os dados"
        )
        
        if st.button("🔄 Atualizar Dashboard"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.header("🏢 Filtros por Entidade")
        
        # Filtro de Estado/Entidade
        estado_options = ['PE', 'RN']
        estado_filter = st.multiselect(
            "Filtrar por Estado",
            options=estado_options,
            default=estado_options,
            help="PE: Ticket > TI > Cng PE | RN: Ticket > TI > Cng PE > Cng RN"
        )
        
        st.markdown("---")
        st.header("📅 Filtros por Período")
        
        # Carrega dados temporariamente para obter as opções de mês
        df_temp = load_data(uploaded_file)
        if df_temp is not None:
            df_temp_processed = preprocess_sla_data(df_temp)
            # Aplica filtro de estado para obter meses relevantes
            if estado_filter and len(estado_filter) > 0:
                df_temp_processed = df_temp_processed[df_temp_processed['Estado'].isin(estado_filter)]
            
            # Obtém lista única de meses disponíveis
            months_available = sorted(df_temp_processed['Ano_Mes'].dropna().unique().astype(str))
            
            if months_available:
                month_filter = st.multiselect(
                    "Filtrar por Mês/Ano",
                    options=months_available,
                    default=months_available,
                    help="Filtro aplicado apenas às seções: Resumo Geral SLA, Métricas Gerais, Análise de SLA, Top 10 Departamentos, Tickets por Localização e Distribuição por Técnico"
                )
            else:
                month_filter = []
        else:
            month_filter = []
    
    # Carrega os dados
    df = load_data(uploaded_file)
    
    if df is None:
        st.error("❌ Não foi possível carregar os dados. Verifique se o arquivo glpi.csv existe no diretório.")
        return
    
    # Métricas principais
    st.header("📊 Métricas Gerais")
    
    # Processa dados com filtros
    df_sla = preprocess_sla_data(df)
    
    # Aplica filtro de estado
    if estado_filter and len(estado_filter) > 0:
        df_sla = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês para as métricas gerais
    if month_filter and len(month_filter) > 0:
        df_sla = df_sla[df_sla['Ano_Mes'].astype(str).isin(month_filter)]
    
    # Os dados já estão filtrados pelo time na função load_data
    df_filtered = df_sla
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tickets = len(df_filtered)
        st.metric("Total de Tickets", total_tickets)
    
    with col2:
        pendentes = len(df_filtered[df_filtered['Status'] == 'Pendente'])
        st.metric("Pendentes", pendentes)
    
    with col3:
        em_atendimento = len(df_filtered[df_filtered['Status'] == 'Em atendimento (atribuído)'])
        st.metric("Em Atendimento", em_atendimento)
    
    with col4:
        solucionados = len(df_filtered[df_filtered['Status'] == 'Solucionado'])
        st.metric("Solucionados", solucionados)
        
    with col5:
        fechados = len(df_filtered[df_filtered['Status'] == 'Fechado'])
        st.metric("Fechados", fechados)
    
    st.markdown("---")
    
    # Evolução Mensal
    st.plotly_chart(create_monthly_timeline_chart(df, estado_filter), width='stretch')
    
    st.markdown("---")
    
    # Resumo Geral SLA
    st.header("📋 Resumo Geral SLA ")
    
    # Métricas gerais de SLA (usando mesmo filtro das métricas gerais)
    df_sla_geral = df_filtered
    
    total_sla = len(df_sla_geral)
    dentro_prazo_geral = len(df_sla_geral[~df_sla_geral['SLA_Excedido']])
    fora_prazo_geral = len(df_sla_geral[df_sla_geral['SLA_Excedido']])
    perc_dentro_geral = (dentro_prazo_geral / total_sla * 100) if total_sla > 0 else 0
    perc_fora_geral = (fora_prazo_geral / total_sla * 100) if total_sla > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📊 Geral", 
            f"{total_sla} tickets",
            help="Total de tickets nas categorias principais"
        )
    
    with col2:
        st.metric(
            "✅ Dentro do Prazo", 
            f"{dentro_prazo_geral} ({perc_dentro_geral:.1f}%)",
            delta=f"{perc_dentro_geral:.1f}%",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "⚠️ Fora do Prazo", 
            f"{fora_prazo_geral} ({perc_fora_geral:.1f}%)",
            delta=f"{perc_fora_geral:.1f}%",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Análise de SLA
    st.header("📈 Análise de SLA")
    
    # SLA Metrics em linha horizontal com fonte menor
    df_sla = preprocess_sla_data(df)
    
    # Aplica filtro de estado para métricas
    if estado_filter and len(estado_filter) > 0:
        df_sla = df_sla[df_sla['Estado'].isin(estado_filter)]
    
    # Aplica filtro de mês para análise de SLA
    if month_filter and len(month_filter) > 0:
        df_sla = df_sla[df_sla['Ano_Mes'].astype(str).isin(month_filter)]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Métricas TI Infra
        ti_infra = df_sla[df_sla['Categoria_SLA'] == 'TI Infra']
        infra_total = len(ti_infra)
        infra_dentro = len(ti_infra[~ti_infra['SLA_Excedido']])
        infra_fora = len(ti_infra[ti_infra['SLA_Excedido']])
        infra_perc = (infra_dentro / infra_total * 100) if infra_total > 0 else 0
        
        st.markdown("<h4 style='font-size: 16px;'>🔧 Infra</h4>", unsafe_allow_html=True)
        st.metric("Total", infra_total, label_visibility="visible")
        st.metric("Dentro do Prazo", f"{infra_dentro} ({infra_perc:.1f}%)")
        st.metric("Fora do Prazo", f"{infra_fora} ({100-infra_perc:.1f}%)")
    
    with col2:
        # Métricas TI Sistema GPM
        ti_gpm = df_sla[df_sla['Categoria_SLA'] == 'TI Sistema GPM']
        gpm_total = len(ti_gpm)
        gpm_dentro = len(ti_gpm[~ti_gpm['SLA_Excedido']])
        gpm_fora = len(ti_gpm[ti_gpm['SLA_Excedido']])
        gmp_perc = (gpm_dentro / gpm_total * 100) if gpm_total > 0 else 0
        
        st.markdown("<h4 style='font-size: 16px;'>📊 GPM</h4>", unsafe_allow_html=True)
        st.metric("Total", gpm_total)
        st.metric("Dentro do Prazo", f"{gpm_dentro} ({gmp_perc:.1f}%)")
        st.metric("Fora do Prazo", f"{gpm_fora} ({100-gmp_perc:.1f}%)")
    
    with col3:
        # Métricas TI Sistema Telefonia
        ti_tel = df_sla[df_sla['Categoria_SLA'] == 'TI Sistema Telefonia']
        tel_total = len(ti_tel)
        tel_dentro = len(ti_tel[~ti_tel['SLA_Excedido']])
        tel_fora = len(ti_tel[ti_tel['SLA_Excedido']])
        tel_perc = (tel_dentro / tel_total * 100) if tel_total > 0 else 0
        
        st.markdown("<h4 style='font-size: 16px;'>📞 Telefonia</h4>", unsafe_allow_html=True)
        st.metric("Total", tel_total)
        st.metric("Dentro do Prazo", f"{tel_dentro} ({tel_perc:.1f}%)")
        st.metric("Fora do Prazo", f"{tel_fora} ({100-tel_perc:.1f}%)")
    
    st.markdown("---")
    
    # Compliance SLA por Mês
    st.header("📉 Compliance SLA")
    st.plotly_chart(create_sla_compliance_chart(df, estado_filter, month_filter), width='stretch')
    
    st.markdown("---")
    
    # Gráficos por departamento e localização
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_department_chart(df, estado_filter, month_filter), width='stretch')
    
    with col2:
        st.plotly_chart(create_location_chart(df, estado_filter, month_filter), width='stretch')
    
    st.markdown("---")
    
    # Gráfico de técnicos
    tech_chart = create_technician_chart(df, estado_filter, month_filter)
    if tech_chart:
        st.plotly_chart(tech_chart, width='stretch')
    
    # Tabela de dados filtráveis
    st.header("📋 Dados Detalhados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filtrar por Status",
            options=df['Status'].unique(),
            default=df['Status'].unique()
        )
    
    with col2:
        priority_filter = st.multiselect(
            "Filtrar por Prioridade",
            options=df['Prioridade'].unique(),
            default=df['Prioridade'].unique()
        )
    
    with col3:
        dept_filter = st.multiselect(
            "Filtrar por Departamento",
            options=df['Plug-ins - Departamento - Departamento'].unique(),
            default=df['Plug-ins - Departamento - Departamento'].unique()
        )
    
    # Aplica filtros nos dados já processados e filtrados pelo time
    df_table = df_filtered.copy()
    
    # Aplica filtros adicionais
    filtered_df = df_table[
        (df_table['Status'].isin(status_filter)) &
        (df_table['Prioridade'].isin(priority_filter)) &
        (df_table['Plug-ins - Departamento - Departamento'].isin(dept_filter))
    ]
    
    # Exibe tabela filtrada
    st.dataframe(filtered_df, width='stretch')
    
    # Informações sobre os dados
    st.sidebar.markdown("---")
    st.sidebar.info(f"📈 Total de registros: {len(df)}")
    st.sidebar.info(f"🔍 Registros filtrados: {len(filtered_df)}")
    
    if uploaded_file:
        st.sidebar.success("✅ Dados carregados do arquivo enviado!")
    else:
        st.sidebar.info("📄 Usando arquivo padrão: glpi.csv")

if __name__ == "__main__":
    main()