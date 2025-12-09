import os
import sqlite3
import pandas as pd
from pathlib import Path

def criar_tabela_fee_based(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_cliente TEXT,
            nome_cliente TEXT,
            data_contratacao TEXT,
            taxa_contratacao REAL,
            excecao_rv TEXT,
            resgate_em_fundo TEXT,
            codigo_assessor TEXT,
            status TEXT,
            pl REAL
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigo_cliente ON dados(codigo_cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nome_cliente ON dados(nome_cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_contratacao ON dados(data_contratacao)')
    conn.commit()

def criar_tabela_receitas(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_relatorio TEXT,
            relatorio TEXT,
            fonte_receita TEXT,
            linha_receita TEXT,
            categoria TEXT,
            produto TEXT,
            detalhe_nivel_1 TEXT,
            detalhe_nivel_2 TEXT,
            detalhe_nivel_3 TEXT,
            detalhe_nivel_4 TEXT,
            data_operacao TEXT,
            cliente TEXT,
            assessor TEXT,
            mesa TEXT,
            empresa TEXT,
            receita_bruta_total REAL,
            receita_liquida_total REAL,
            repasse_escritorio_percentual REAL,
            receita_bruta_escritorio REAL,
            imposto_percentual REAL,
            imposto_valor REAL,
            receita_liquida_escritorio REAL,
            repasse_dbv_percentual REAL,
            repasse_dbv_valor REAL,
            repasse_mesa_percentual REAL,
            repasse_mesa_valor REAL,
            repasse_assessor_percentual REAL,
            repasse_assessor_valor REAL,
            mes_ano TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_operacao ON dados(data_operacao)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mes_ao ON dados(mes_ano)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_linha_receita ON dados(linha_receita)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessor ON dados(assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cliente ON dados(cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_empresa ON dados(empresa)')
    conn.commit()

def criar_tabela_habilitacoes(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT,
            codigo_matriz INTEGER,
            matriz TEXT,
            codigo_assessor TEXT,
            comercial TEXT,
            lead_start REAL,
            meta_lead_start REAL,
            carteiras_simuladas_novos_clientes REAL,
            meta_carteiras_simuladas_novos_clientes REAL,
            habilitacoes_mais_300k REAL,
            meta_habilitacoes_mais_300k REAL,
            habilitacoes_menos_300k REAL,
            meta_habilitacoes_menos_300k REAL,
            conversao_mais_300k REAL,
            meta_conversao_mais_300k REAL,
            conversao_menos_300k REAL,
            meta_conversao_menos_300k REAL,
            perc_contas_acessadas_hub_mais_300k REAL,
            meta_perc_contas_acessadas_hub_mais_300k REAL,
            perc_contas_acessadas_hub_menos_300k REAL,
            meta_perc_contas_acessadas_hub_menos_300k REAL,
            perc_contas_mais_300k_com_ordem_enviada REAL,
            meta_perc_contas_mais_300k_com_ordem_enviada REAL,
            perc_contas_menos_300k_com_ordem_enviada REAL,
            meta_perc_contas_menos_300k_com_ordem_enviada REAL,
            perc_contas_aportaram_mais_300k REAL,
            meta_perc_contas_aportaram_mais_300k REAL,
            perc_contas_aportaram_menos_300k REAL,
            meta_perc_contas_aportaram_menos_300k REAL
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_codigo_assessor ON dados(codigo_assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_ano_mes ON dados(ano_mes)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_matriz ON dados(matriz)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_comercial ON dados(comercial)')
    conn.commit()

def criar_tabela_transferencias(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo INTEGER,
            codigo_assessor_origem TEXT,
            nome_assessor_origem TEXT,
            codigo_assessor_destino TEXT,
            nome_assessor_destino TEXT,
            data_solicitacao TEXT,
            data_transferencia TEXT,
            origem_solicitacao TEXT,
            tipo TEXT,
            status TEXT,
            codigo_solicitacao TEXT,
            cliente TEXT,
            pl REAL
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_codigo_assessor_origem ON dados(codigo_assessor_origem)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_codigo_assessor_destino ON dados(codigo_assessor_destino)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_data_solicitacao ON dados(data_solicitacao)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_data_transferencia ON dados(data_transferencia)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_status ON dados(status)')
    conn.commit()

def criar_tabela_positivador(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positivador (
            Assessor TEXT,
            Cliente TEXT,
            Profissao TEXT,
            Sexo TEXT,
            Segmento TEXT,
            Data_Cadastro TEXT,
            Fez_Segundo_Aporte TEXT,
            Data_Nascimento TEXT,
            Status TEXT,
            Ativou_em_M TEXT,
            Evadiu_em_M TEXT,
            Operou_Bolsa TEXT,
            Operou_Fundo TEXT,
            Operou_Renda_Fixa TEXT,
            Aplicacao_Financeira_Declarada_Ajustada TEXT,
            Receita_no_Mes TEXT,
            Receita_Bovespa TEXT,
            Receita_Futuros TEXT,
            Receita_RF_Bancarios TEXT,
            Receita_RF_Privados TEXT,
            Receita_RF_Publicos TEXT,
            Captacao_Bruta_em_M TEXT,
            Resgate_em_M TEXT,
            Captacao_Liquida_em_M TEXT,
            Captacao_TED TEXT,
            Captacao_ST TEXT,
            Captacao_OTA TEXT,
            Captacao_RF TEXT,
            Captacao_TD TEXT,
            Captacao_PREV TEXT,
            Net_em_M_1 TEXT,
            Net_Em_M TEXT,
            Net_Renda_Fixa TEXT,
            Net_Fundos_Imobiliarios TEXT,
            Net_Renda_Variavel TEXT,
            Net_Fundos TEXT,
            Net_Financeiro TEXT,
            Net_Previdencia TEXT,
            Net_Outros TEXT,
            Receita_Aluguel TEXT,
            Receita_Complemento_Pacote_Corretagem TEXT,
            Tipo_Pessoa TEXT,
            Data_Posicao TEXT,
            Data_Atualizacao TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_assessor ON positivador(Assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_cliente ON positivador(Cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_data_cadastro ON positivador(Data_Cadastro)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_status ON positivador(Status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_segmento ON positivador(Segmento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_data_posicao ON positivador(Data_Posicao)')
    conn.commit()

def criar_tabela_positivador_mtd(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positivador_mtd (
            Assessor TEXT,
            Cliente TEXT,
            Profissao TEXT,
            Sexo TEXT,
            Segmento TEXT,
            Data_Cadastro TEXT,
            Fez_Segundo_Aporte TEXT,
            Data_Nascimento TEXT,
            Status TEXT,
            Ativou_em_M TEXT,
            Evadiu_em_M TEXT,
            Operou_Bolsa TEXT,
            Operou_Fundo TEXT,
            Operou_Renda_Fixa TEXT,
            Aplicacao_Financeira_Declarada_Ajustada TEXT,
            Receita_no_Mes TEXT,
            Receita_Bovespa TEXT,
            Receita_Futuros TEXT,
            Receita_RF_Bancarios TEXT,
            Receita_RF_Privados TEXT,
            Receita_RF_Publicos TEXT,
            Captacao_Bruta_em_M TEXT,
            Resgate_em_M TEXT,
            Captacao_Liquida_em_M TEXT,
            Captacao_TED TEXT,
            Captacao_ST TEXT,
            Captacao_OTA TEXT,
            Captacao_RF TEXT,
            Captacao_TD TEXT,
            Captacao_PREV TEXT,
            Net_em_M_1 TEXT,
            Net_Em_M TEXT,
            Net_Renda_Fixa TEXT,
            Net_Fundos_Imobiliarios TEXT,
            Net_Renda_Variavel TEXT,
            Net_Fundos TEXT,
            Net_Financeiro TEXT,
            Net_Previdencia TEXT,
            Net_Outros TEXT,
            Receita_Aluguel TEXT,
            Receita_Complemento_Pacote_Corretagem TEXT,
            Tipo_Pessoa TEXT,
            Data_Posicao TEXT,
            Data_Atualizacao TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_assessor ON positivador_mtd(Assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_cliente ON positivador_mtd(Cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_data_cadastro ON positivador_mtd(Data_Cadastro)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_status ON positivador_mtd(Status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_segmento ON positivador_mtd(Segmento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_data_posicao ON positivador_mtd(Data_Posicao)')
    conn.commit()

def criar_tabela_diversificador(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessor TEXT,
            cliente TEXT,
            produto TEXT,
            sub_produto TEXT,
            produto_em_garantia TEXT,
            cnpj_fundo TEXT,
            ativo TEXT,
            emissor TEXT,
            data_vencimento TEXT,
            quantidade REAL,
            net REAL,
            data TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_assessor ON dados(assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_cliente ON dados(cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_produto ON dados(produto)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_data ON dados(data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_vcto ON dados(data_vencimento)')
    conn.commit()

# NOVO: tabela Produtos
def criar_tabela_produtos(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            produto TEXT,
            apolice_grupo_cota TEXT,
            valor_negocio REAL,
            fonte_receita TEXT,
            linha_receita TEXT,
            categoria TEXT,
            nome_cliente TEXT,
            codigo_dbv TEXT,
            codigo_xp TEXT,
            codigo_assessor TEXT,
            mesa TEXT,
            empresa TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_data ON dados(data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_produto ON dados(produto)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON dados(categoria)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_assessor ON dados(codigo_assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_cliente ON dados(nome_cliente)')
    conn.commit()

# NOVO: tabela MesaRV
def criar_tabela_mesarv(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mesarv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            cliente TEXT,
            assessor TEXT,
            tipo TEXT,
            mandato TEXT,
            classe TEXT,
            auc REAL
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_data ON mesarv(data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_assessor ON mesarv(assessor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_cliente ON mesarv(cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_classe ON mesarv(classe)')
    conn.commit()

def criar_tabela_clientes(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xp_1 TEXT,
            xp_2 TEXT,
            xp_3 TEXT,
            nome TEXT,
            codigo_dbv TEXT
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clientes_codigo ON clientes(codigo_dbv)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome)')
    conn.commit()

def criar_tabela_objetivos(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objetivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            auc_total REAL,
            captacao_total_diaria REAL,
            captacao_mensal REAL,
            receita_diaria REAL,
            receita_mensal REAL
        )
    ''')
    conn.commit()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_objetivos_data ON objetivos(data)')
    conn.commit()


def importar_csv_para_sqlite(caminho_arquivo, caminho_saida, tipo):
    """
    Importa um arquivo CSV para um banco de dados SQLite.

    tipo: 'feebased', 'receitas', 'habilitacoes', 'transferencias', 'positivador', 'diversificador' ou 'produtos'
    """
    conn = None
    try:
        if os.path.exists(caminho_saida):
            try:
                if conn is not None:
                    conn.close()
            except:
                pass
            try:
                os.remove(caminho_saida)
            except PermissionError:
                print(f"Erro: Não foi possível remover {caminho_saida}. Feche programas que estejam usando o arquivo.")
                return

        conn = sqlite3.connect(caminho_saida)

        if tipo == 'feebased':
            criar_tabela_fee_based(conn)
        elif tipo == 'receitas':
            criar_tabela_receitas(conn)
        elif tipo == 'habilitacoes':
            criar_tabela_habilitacoes(conn)
        elif tipo == 'transferencias':
            criar_tabela_transferencias(conn)
        elif tipo == 'positivador':
            criar_tabela_positivador(conn)
        elif tipo == 'diversificador':
            criar_tabela_diversificador(conn)
        elif tipo == 'produtos':
            criar_tabela_produtos(conn)
        elif tipo == 'mesarv':
            criar_tabela_mesarv(conn)
        elif tipo == 'clientes':
            criar_tabela_clientes(conn)
        elif tipo == 'objetivos':
            criar_tabela_objetivos(conn)
        elif tipo == 'positivador_mtd':
            criar_tabela_positivador_mtd(conn)
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {tipo}")

        # Mapas de colunas
        fee_based_columns_map = {
            'Código Cliente': 'codigo_cliente',
            'Nome Cliente': 'nome_cliente',
            'Data Contratação': 'data_contratacao',
            'Taxa Contratação': 'taxa_contratacao',
            'Exceção RV': 'excecao_rv',
            'Resgate em fundo': 'resgate_em_fundo',
            'Código Assessor': 'codigo_assessor',
            'Status': 'status',
            'P/L': 'pl'
        }

        receitas_columns_map = {
            'Data Relatório': 'data_relatorio',
            'Relatório': 'relatorio',
            'Fonte Receita': 'fonte_receita',
            'Linha Receita': 'linha_receita',
            'Categoria': 'categoria',
            'Produto': 'produto',
            'Detalhe Nível 1': 'detalhe_nivel_1',
            'Detalhe Nível 2': 'detalhe_nivel_2',
            'Detalhe Nível 3': 'detalhe_nivel_3',
            'Detalhe Nível 4': 'detalhe_nivel_4',
            'Data': 'data_operacao',
            'Cliente': 'cliente',
            'Assessor': 'assessor',
            'Mesa': 'mesa',
            'Empresa': 'empresa',
            'Receita Bruta Total (R$)': 'receita_bruta_total',
            'Receita Líquida Total (R$)': 'receita_liquida_total',
            'Repasse (%) Escritório': 'repasse_escritorio_percentual',
            'Receita Bruta Escritório (R$)': 'receita_bruta_escritorio',
            'Imposto (%)': 'imposto_percentual',
            'Imposto (R$)': 'imposto_valor',
            'Receita Líquida Escritório (R$)': 'receita_liquida_escritorio',
            'Repasse DBV (%)': 'repasse_dbv_percentual',
            'Repasse DBV (R$)': 'repasse_dbv_valor',
            'Repasse Mesa (%)': 'repasse_mesa_percentual',
            'Repasse Mesa (R$)': 'repasse_mesa_valor',
            'Repasse Assessor (%)': 'repasse_assessor_percentual',
            'Repasse Assessor (R$)': 'repasse_assessor_valor'
        }

        habilitacoes_columns_map = {
            'Ano/Mês': 'ano_mes',
            'Código Matriz': 'codigo_matriz',
            'Matriz': 'matriz',
            'Código Assessor': 'codigo_assessor',
            'Comercial?': 'comercial',
            'Lead Start': 'lead_start',
            'Meta Lead Start': 'meta_lead_start',
            'Carteiras Simuladas Novos Clientes': 'carteiras_simuladas_novos_clientes',
            'Meta Carteiras Simuladas Novos Clientes': 'meta_carteiras_simuladas_novos_clientes',
            'Habilitações +300k': 'habilitacoes_mais_300k',
            'Meta Habilitações +300k': 'meta_habilitacoes_mais_300k',
            'Habilitações -300k': 'habilitacoes_menos_300k',
            'Meta Habilitações -300k': 'meta_habilitacoes_menos_300k',
            'Conversão +300k': 'conversao_mais_300k',
            'Meta Conversão +300k': 'meta_conversao_mais_300k',
            'Conversão -300k': 'conversao_menos_300k',
            'Meta Conversão -300k': 'meta_conversao_menos_300k',
            '% Contas Acessadas no Hub +300k': 'perc_contas_acessadas_hub_mais_300k',
            'Meta % Contas Acessadas no Hub +300k': 'meta_perc_contas_acessadas_hub_mais_300k',
            '% Contas Acessadas no Hub -300k': 'perc_contas_acessadas_hub_menos_300k',
            'Meta % Contas Acessadas no Hub -300k': 'meta_perc_contas_acessadas_hub_menos_300k',
            '% Contas +300k com Ordem Enviada': 'perc_contas_mais_300k_com_ordem_enviada',
            'Meta % Contas +300k com Ordem Enviada': 'meta_perc_contas_mais_300k_com_ordem_enviada',
            '% Contas -300k com Ordem Enviada': 'perc_contas_menos_300k_com_ordem_enviada',
            'Meta % Contas -300k com Ordem Enviada': 'meta_perc_contas_menos_300k_com_ordem_enviada',
            '% Contas que Aportaram +300k': 'perc_contas_aportaram_mais_300k',
            'Meta % Contas que Aportaram +300k': 'meta_perc_contas_aportaram_mais_300k',
            '% Contas que Aportaram -300k': 'perc_contas_aportaram_menos_300k',
            'Meta % Contas que Aportaram -300k': 'meta_perc_contas_aportaram_menos_300k'
        }

        transferencias_columns_map = {
            'Código': 'codigo_cliente',
            'Código Assessor Origem': 'codigo_assessor_origem',
            'Nome Assessor Origem': 'nome_assessor_origem',
            'Código Assessor Destino': 'codigo_assessor_destino',
            'Nome Assessor Destino': 'nome_assessor_destino',
            'Data Solicitação': 'data_solicitacao',
            'Data Transferência': 'data_transferencia',
            'Origem Solicitação': 'origem_solicitacao',
            'Tipo': 'tipo',
            'Status': 'status',
            'Código Solicitação': 'codigo_solicitacao',
            'Cliente': 'cliente',
            'PL': 'pl'
        }

        diversificador_columns_map = {
            'Assessor': 'assessor',
            'Cliente': 'cliente',
            'Produto': 'produto',
            'Sub Produto': 'sub_produto',
            'Produto em Garantia': 'produto_em_garantia',
            'CNPJ Fundo': 'cnpj_fundo',
            'Ativo': 'ativo',
            'Emissor': 'emissor',
            'Data de Vencimento': 'data_vencimento',
            'Quantidade': 'quantidade',
            'NET': 'net',
            'Data': 'data'
        }

        positivador_columns_map = {
            'Assessor': 'Assessor',
            'Cliente': 'Cliente',
            'Profissǜo': 'Profissao',
            'Sexo': 'Sexo',
            'Segmento': 'Segmento',
            'Data de Cadastro': 'Data_Cadastro',
            'Fez Segundo Aporte?': 'Fez_Segundo_Aporte',
            'Data de Nascimento': 'Data_Nascimento',
            'Status': 'Status',
            'Ativou em M?': 'Ativou_em_M',
            'Evadiu em M?': 'Evadiu_em_M',
            'Operou Bolsa?': 'Operou_Bolsa',
            'Operou Fundo?': 'Operou_Fundo',
            'Operou Renda Fixa?': 'Operou_Renda_Fixa',
            'Aplicação Financeira Declarada Ajustada': 'Aplicacao_Financeira_Declarada_Ajustada',
            'Receita no Mês': 'Receita_no_Mes',
            'Receita Bovespa': 'Receita_Bovespa',
            'Receita Futuros': 'Receita_Futuros',
            'Receita RF Bancários': 'Receita_RF_Bancarios',
            'Receita RF Privados': 'Receita_RF_Privados',
            'Receita RF Públicos': 'Receita_RF_Publicos',
            'Captação Bruta em M': 'Captacao_Bruta_em_M',
            'Resgate em M': 'Resgate_em_M',
            'Captação Líquida em M': 'Captacao_Liquida_em_M',
            'Captação TED': 'Captacao_TED',
            'Captação ST': 'Captacao_ST',
            'Captação OTA': 'Captacao_OTA',
            'Captação RF': 'Captacao_RF',
            'Captação TD': 'Captacao_TD',
            'Captação PREV': 'Captacao_PREV',
            'Net em M 1': 'Net_em_M_1',
            'Net Em M': 'Net_Em_M',
            'Net Renda Fixa': 'Net_Renda_Fixa',
            'Net Fundos Imobiliários': 'Net_Fundos_Imobiliarios',
            'Net Renda Variável': 'Net_Renda_Variavel',
            'Net Fundos': 'Net_Fundos',
            'Net Financeiro': 'Net_Financeiro',
            'Net Previdência': 'Net_Previdencia',
            'Net Outros': 'Net_Outros',
            'Receita Aluguel': 'Receita_Aluguel',
            'Receita Complemento Pacote Corretagem': 'Receita_Complemento_Pacote_Corretagem',
            'Tipo Pessoa': 'Tipo_Pessoa',
            'Data Posição': 'Data_Posicao',
            'Data Atualização': 'Data_Atualizacao'
        }

        positivador_mtd_columns_map = {
            'Assessor': 'Assessor',
            'Cliente': 'Cliente',
            'Profissǜo': 'Profissao',
            'Sexo': 'Sexo',
            'Segmento': 'Segmento',
            'Data de Cadastro': 'Data_Cadastro',
            'Fez Segundo Aporte?': 'Fez_Segundo_Aporte',
            'Data de Nascimento': 'Data_Nascimento',
            'Status': 'Status',
            'Ativou em M?': 'Ativou_em_M',
            'Evadiu em M?': 'Evadiu_em_M',
            'Operou Bolsa?': 'Operou_Bolsa',
            'Operou Fundo?': 'Operou_Fundo',
            'Operou Renda Fixa?': 'Operou_Renda_Fixa',
            'Aplicação Financeira Declarada Ajustada': 'Aplicacao_Financeira_Declarada_Ajustada',
            'Receita no Mês': 'Receita_no_Mes',
            'Receita Bovespa': 'Receita_Bovespa',
            'Receita Futuros': 'Receita_Futuros',
            'Receita RF Bancários': 'Receita_RF_Bancarios',
            'Receita RF Privados': 'Receita_RF_Privados',
            'Receita RF Públicos': 'Receita_RF_Publicos',
            'Captação Bruta em M': 'Captacao_Bruta_em_M',
            'Resgate em M': 'Resgate_em_M',
            'Captação Líquida em M': 'Captacao_Liquida_em_M',
            'Captação TED': 'Captacao_TED',
            'Captação ST': 'Captacao_ST',
            'Captação OTA': 'Captacao_OTA',
            'Captação RF': 'Captacao_RF',
            'Captação TD': 'Captacao_TD',
            'Captação PREV': 'Captacao_PREV',
            'Net em M 1': 'Net_em_M_1',
            'Net Em M': 'Net_Em_M',
            'Net Renda Fixa': 'Net_Renda_Fixa',
            'Net Fundos Imobiliários': 'Net_Fundos_Imobiliarios',
            'Net Renda Variável': 'Net_Renda_Variavel',
            'Net Fundos': 'Net_Fundos',
            'Net Financeiro': 'Net_Financeiro',
            'Net Previdência': 'Net_Previdencia',
            'Net Outros': 'Net_Outros',
            'Receita Aluguel': 'Receita_Aluguel',
            'Receita Complemento Pacote Corretagem': 'Receita_Complemento_Pacote_Corretagem',
            'Tipo Pessoa': 'Tipo_Pessoa',
            'Data Posição': 'Data_Posicao',
            'Data Atualização': 'Data_Atualizacao'
        }

        # NOVO: mapa Produtos
        produtos_columns_map = {
            'Data': 'data',
            'Produto': 'produto',
            'Apólice/Grupo/Cota': 'apolice_grupo_cota',
            'Valor Negócio (R$)': 'valor_negocio',
            'Fonte Receita': 'fonte_receita',
            'Linha Receita': 'linha_receita',
            'Categoria': 'categoria',
            'Nome Cliente': 'nome_cliente',
            'Código DBV': 'codigo_dbv',
            'Código XP': 'codigo_xp',
            'Código Assessor': 'codigo_assessor',
            'Mesa': 'mesa',
            'Empresa': 'empresa'
        }

        mesarv_columns_map = {
            'Data': 'data',
            'Cliente': 'cliente',
            'Assessor': 'assessor',
            'Tipo': 'tipo',
            'Mandato': 'mandato',
            'Classe': 'classe',
            'AUC': 'auc'
        }

        clientes_columns_map = {
            'XP 1': 'xp_1',
            'XP 2': 'xp_2',
            'XP 3': 'xp_3',
            'Nome': 'nome',
            'Código DBV': 'codigo_dbv'
        }

        objetivos_columns_map = {
            'Data': 'data',
            'AUC Total': 'auc_total',
            'Captação Total (Diária)': 'captacao_total_diaria',
            'Captação Mensal': 'captacao_mensal',
            'Receita Diária': 'receita_diaria',
            'Receita Mensal': 'receita_mensal'
        }


        # Função auxiliar para limpar IDs numéricos (remover .0)
        def clean_numeric_id(x):
            if pd.isna(x):
                return x
            s = str(x).strip()
            # Remove .0 do final da string se existir
            if s.endswith('.0'):
                return s[:-2]
            return s

        # Escolhe o mapeamento
        if tipo == 'feebased':
            columns_map = fee_based_columns_map
        elif tipo == 'receitas':
            columns_map = receitas_columns_map
        elif tipo == 'habilitacoes':
            columns_map = habilitacoes_columns_map
        elif tipo == 'transferencias':
            columns_map = transferencias_columns_map
        elif tipo == 'positivador':
            columns_map = positivador_columns_map
        elif tipo == 'diversificador':
            columns_map = diversificador_columns_map
        elif tipo == 'produtos':
            columns_map = produtos_columns_map
        elif tipo == 'mesarv':
            columns_map = mesarv_columns_map
        elif tipo == 'clientes':
            columns_map = clientes_columns_map
        elif tipo == 'objetivos':
            columns_map = objetivos_columns_map
        elif tipo == 'positivador_mtd':
            columns_map = positivador_mtd_columns_map
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {tipo}")

        # -------- PARSER ROBUSTO (já usado no Diversificador e reaproveitado) --------
        def parse_number_br_robusto(x):
            if x is None:
                return None
            s = str(x).strip()
            if s == '' or s == '-':
                return None
            s = s.replace('R$', '').replace(' ', '')
            if '.' in s and ',' in s:
                s = s.replace('.', '').replace(',', '.')
            elif ',' in s:
                s = s.replace(',', '.')
            try:
                return float(s)
            except ValueError:
                return None
        # ----------------------------------------------------------------------------

        chunksize = 10000
        first_chunk = True

        for chunk in pd.read_csv(caminho_arquivo, encoding='utf-8', sep=',', chunksize=chunksize, dtype=str):
            chunk.columns = chunk.columns.str.strip()
            chunk = chunk.rename(columns={k: v for k, v in columns_map.items() if k in chunk.columns})
            chunk = chunk[[col for col in columns_map.values() if col in chunk.columns]]

            if first_chunk and chunk.shape[1] == 0:
                raise RuntimeError("Nenhuma coluna mapeada. Verifique separador/encoding do arquivo.")

            # normaliza ausentes
            chunk = chunk.fillna('')

            # ----------- CLIENTES -----------
            if tipo == 'clientes':
                # Limpa os campos XP e código DBV (remove .0)
                for col in ['xp_1', 'xp_2', 'xp_3', 'codigo_dbv']:
                    if col in chunk.columns:
                        chunk[col] = chunk[col].apply(clean_numeric_id)
                
                # Remove linhas vazias
                chunk = chunk[chunk['codigo_dbv'] != '']

            # ----------- DIVERSIFICADOR (como já corrigido) -----------
            elif tipo == 'diversificador':
                for col in ('quantidade', 'net'):
                    if col in chunk.columns:
                        chunk[col] = chunk[col].apply(parse_number_br_robusto)
                for col in ('data_vencimento', 'data'):
                    if col in chunk.columns:
                        chunk[col] = pd.to_datetime(chunk[col], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')

            # ----------- NOVO: PRODUTOS (ISO-first, sem inversão) -----------------
            import re

            if tipo == 'produtos':
                # 1) valor: número BR robusto
                if 'valor_negocio' in chunk.columns:
                    chunk['valor_negocio'] = chunk['valor_negocio'].apply(parse_number_br_robusto)

                # 2) datas: prioriza YYYY-MM-DD; depois BR quando necessário
                def parse_data_produtos(x):
                    s = ('' if x is None else str(x)).strip()

                    # vazio / nulos
                    if s == '' or s.lower() in ('nat', 'nan', 'none', '-'):
                        return pd.NaT

                    # serial Excel?
                    try:
                        v = float(s)
                        if 1 <= v <= 60000:
                            return pd.to_datetime(v, origin='1899-12-30', unit='D', errors='coerce')
                    except Exception:
                        pass

                    # ISO estrito: YYYY-MM-DD ou YYYY/MM/DD (NUNCA dayfirst aqui)
                    if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', s):
                        return pd.to_datetime(s.replace('/', '-'), format='%Y-%m-%d', errors='coerce')

                    # MM/YYYY -> dia 01 (constrói ISO e parseia sem dayfirst)
                    mmyyyy = re.match(r'^(\d{2})/(\d{4})$', s)
                    if mmyyyy:
                        m, y = mmyyyy.group(1), mmyyyy.group(2)
                        return pd.to_datetime(f'{y}-{m}-01', format='%Y-%m-%d', errors='coerce')

                    # BR: DD/MM/YYYY ou DD-MM-YYYY (aqui sim dayfirst)
                    if re.match(r'^\d{2}/\d{2}/\d{4}$', s):
                        return pd.to_datetime(s, format='%d/%m/%Y', errors='coerce')
                    if re.match(r'^\d{2}-\d{2}-\d{4}$', s):
                        return pd.to_datetime(s, format='%d-%m-%Y', errors='coerce')

                    # fallback: tenta sem dayfirst
                    return pd.to_datetime(s, errors='coerce')

                if 'data' in chunk.columns:
                    dt = chunk['data'].apply(parse_data_produtos)
                    dt = pd.to_datetime(dt, errors='coerce').dt.tz_localize(None).dt.normalize()
                    chunk['data'] = dt.dt.strftime('%Y-%m-%d')

                # 3) Higieniza textos
                text_cols = [
                    'produto', 'apolice_grupo_cota', 'fonte_receita', 'linha_receita',
                    'categoria', 'nome_cliente', 'codigo_dbv', 'codigo_xp',
                    'codigo_assessor', 'mesa', 'empresa'
                ]
                for col in [c for c in text_cols if c in chunk.columns]:
                    chunk[col] = (chunk[col]
                                .astype(str)
                                .str.replace(r'^\s*-\s*$', '', regex=True)
                                .str.strip())
            # ----------------------------------------------------------------------
            if tipo == 'mesarv':
                # Converter AUC
                if 'auc' in chunk.columns:
                    chunk['auc'] = chunk['auc'].apply(parse_number_br_robusto)

                # Converter datas (YYYY-MM-DD, DD/MM/YYYY, serial Excel)
                def parse_data_mesarv(x):
                    s = ('' if x is None else str(x)).strip()
                    if s == '' or s.lower() in ('nat', 'nan', 'none', '-'):
                        return pd.NaT
                    try:
                        v = float(s)
                        if 1 <= v <= 60000:
                            return pd.to_datetime(v, origin='1899-12-30', unit='D', errors='coerce')
                    except:
                        pass
                    return pd.to_datetime(s, errors='coerce', dayfirst=True)

                if 'data' in chunk.columns:
                    dt = chunk['data'].apply(parse_data_mesarv)
                    dt = pd.to_datetime(dt, errors='coerce').dt.tz_localize(None).dt.normalize()
                    chunk['data'] = dt.dt.strftime('%Y-%m-%d')



            # Processamento específico para Objetivos
            if tipo == 'objetivos':
                # Converter valores numéricos
                numeric_cols = ['auc_total', 'captacao_total_diaria', 'captacao_mensal', 'receita_diaria', 'receita_mensal']
                for col in numeric_cols:
                    if col in chunk.columns:
                        chunk[col] = chunk[col].apply(parse_number_br_robusto)
                
                # Processar datas
                if 'data' in chunk.columns:
                    def parse_data_objetivos(x):
                        s = ('' if x is None else str(x)).strip()
                        
                        # vazio / nulos
                        if s == '' or s.lower() in ('nat', 'nan', 'none', '-'):
                            return pd.NaT

                        # serial Excel?
                        try:
                            v = float(s)
                            if 1 <= v <= 60000:
                                return pd.to_datetime(v, origin='1899-12-30', unit='D', errors='coerce')
                        except Exception:
                            pass

                        # ISO estrito: YYYY-MM-DD ou YYYY/MM/DD
                        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', s):
                            return pd.to_datetime(s.replace('/', '-'), format='%Y-%m-%d', errors='coerce')

                        # BR: DD/MM/YYYY ou DD-MM-YYYY
                        if re.match(r'^\d{2}/\d{2}/\d{4}$', s):
                            return pd.to_datetime(s, format='%d/%m/%Y', errors='coerce')
                        if re.match(r'^\d{2}-\d{2}-\d{4}$', s):
                            return pd.to_datetime(s, format='%d-%m-%Y', errors='coerce')

                        # fallback: tenta sem dayfirst
                        return pd.to_datetime(s, errors='coerce')
                    
                    dt = chunk['data'].apply(parse_data_objetivos)
                    dt = pd.to_datetime(dt, errors='coerce').dt.tz_localize(None).dt.normalize()
                    chunk['data'] = dt.dt.strftime('%Y-%m-%d')

            # Processamento específico Receitas (inalterado)
            if tipo == 'receitas':
                def converter_data(data_str):
                    if pd.isna(data_str) or data_str == '':
                        return pd.NaT
                    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%Y%m%d']
                    for fmt in formatos:
                        try:
                            return pd.to_datetime(data_str, format=fmt, errors='raise')
                        except (ValueError, TypeError):
                            continue
                    return pd.NaT

                if 'data_operacao' in chunk.columns:
                    chunk['data_operacao'] = chunk['data_operacao'].apply(converter_data)
                    chunk['mes_ano'] = chunk['data_operacao'].dt.strftime('%Y-%m')
                    datas_invalidas = chunk['data_operacao'].isna().sum()
                    if datas_invalidas > 0:
                        print(f"Aviso: {datas_invalidas} datas de operação não puderam ser convertidas.")

                if 'data_relatorio' in chunk.columns:
                    chunk['data_relatorio'] = chunk['data_relatorio'].apply(converter_data)
                    datas_invalidas = chunk['data_relatorio'].isna().sum()
                    if datas_invalidas > 0:
                        print(f"Aviso: {datas_invalidas} datas de relatório não puderam ser convertidas.")

                def converter_valor(valor):
                    if pd.isna(valor) or valor == '':
                        return 0.0
                    try:
                        if isinstance(valor, str):
                            valor = valor.replace('R$', '').replace(' ', '').strip()
                            if ',' in valor and '.' in valor:
                                valor = valor.replace('.', '').replace(',', '.')
                            elif ',' in valor:
                                valor = valor.replace(',', '.')
                            valor = ''.join(c for c in str(valor) if c.isdigit() or c in '.-')
                        return float(valor) if valor not in ('', '.', '-') else 0.0
                    except (ValueError, TypeError):
                        return 0.0

                colunas_monetarias = [
                    'receita_bruta_total', 'receita_liquida_total', 'receita_bruta_escritorio',
                    'imposto_valor', 'receita_liquida_escritorio', 'repasse_dbv_valor',
                    'repasse_mesa_valor', 'repasse_assessor_valor'
                ]
                for col in [c for c in colunas_monetarias if c in chunk.columns]:
                    chunk[col] = chunk[col].apply(converter_valor)

                def converter_percentual(valor):
                    if pd.isna(valor) or valor == '':
                        return 0.0
                    try:
                        if isinstance(valor, str):
                            valor = valor.replace('%', '').replace(' ', '').strip()
                            valor = valor.replace(',', '.')
                            valor = ''.join(c for c in valor if c.isdigit() or c in '.-')
                        return float(valor) / 100 if valor != '' else 0.0
                    except (ValueError, TypeError):
                        return 0.0

                colunas_percentuais = [
                    'repasse_escritorio_percentual', 'imposto_percentual',
                    'repasse_dbv_percentual', 'repasse_mesa_percentual', 'repasse_assessor_percentual'
                ]
                for col in [c for c in colunas_percentuais if c in chunk.columns]:
                    chunk[col] = chunk[col].apply(converter_percentual)

            # Grava
            if tipo == 'positivador':
                table_name = 'positivador'
            elif tipo == 'positivador_mtd':
                table_name = 'positivador_mtd'
            elif tipo == 'mesarv':
                table_name = 'mesarv'
            else:
                table_name = 'dados'
            chunk.to_sql(table_name, conn, if_exists='replace' if first_chunk else 'append', index=False)

            if first_chunk:
                print(f"Estrutura do arquivo {os.path.basename(caminho_arquivo)}:")
                print("Colunas:", ", ".join([f'"{col}"' for col in chunk.columns]))
                try:
                    total_linhas = sum(1 for _ in open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore')) - 1
                    print(f"Total de linhas a serem processadas: Aproximadamente {total_linhas:,}")
                except Exception:
                    pass
                first_chunk = False

            print(f"Processadas {len(chunk):,} linhas...")

        # Índices extras por tipo (alguns já criados)
        cursor = conn.cursor()
        if tipo == 'feebased':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigo_cliente ON dados(codigo_cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigo_assessor ON dados(codigo_assessor)')
        elif tipo == 'receitas':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_operacao ON dados(data_operacao)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON dados(categoria)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessor ON dados(assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cliente ON dados(cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_empresa ON dados(empresa)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_linha_receita ON dados(linha_receita)')
        elif tipo == 'habilitacoes':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_codigo_assessor ON dados(codigo_assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_ano_mes ON dados(ano_mes)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_matriz ON dados(matriz)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_habilitacoes_comercial ON dados(comercial)')
        elif tipo == 'transferencias':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_codigo_assessor_origem ON dados(codigo_assessor_origem)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_codigo_assessor_destino ON dados(codigo_assessor_destino)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_data_solicitacao ON dados(data_solicitacao)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_data_transferencia ON dados(data_transferencia)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transferencias_status ON dados(status)')
        elif tipo == 'positivador':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_assessor ON positivador(Assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_cliente ON positivador(Cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_data_cadastro ON positivador(Data_Cadastro)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_status ON positivador(Status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_segmento ON positivador(Segmento)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_data_posicao ON positivador(Data_Posicao)')
        elif tipo == 'positivador_mtd':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_assessor ON positivador_mtd(Assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_cliente ON positivador_mtd(Cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_data_cadastro ON positivador_mtd(Data_Cadastro)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_status ON positivador_mtd(Status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_segmento ON positivador_mtd(Segmento)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positivador_mtd_data_posicao ON positivador_mtd(Data_Posicao)')
        elif tipo == 'diversificador':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_assessor ON dados(assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_cliente ON dados(cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_produto ON dados(produto)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_data ON dados(data)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diversificador_vcto ON dados(data_vencimento)')
        elif tipo == 'produtos':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_data ON dados(data)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_produto ON dados(produto)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON dados(categoria)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_assessor ON dados(codigo_assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_cliente ON dados(nome_cliente)')
        elif tipo == 'mesarv':
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_data ON mesarv(data)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_assessor ON mesarv(assessor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_cliente ON mesarv(cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesarv_classe ON mesarv(classe)')

        conn.commit()
        conn.close()

        print(f"\nArquivo {os.path.basename(caminho_arquivo)} convertido com sucesso para SQLite!")
        print(f"Arquivo gerado: {os.path.abspath(caminho_saida)}")

    except Exception as e:
        print(f"\nErro ao processar o arquivo {os.path.basename(caminho_arquivo)}:")
        print(str(e))
        try:
            if conn is not None:
                conn.close()
        except:
            pass
        try:
            if os.path.exists(caminho_saida):
                os.remove(caminho_saida)
        except PermissionError:
            print(f"Aviso: não consegui apagar {caminho_saida} (arquivo em uso). Feche o programa que o está usando.")

def main():
    diretorio = Path(__file__).parent
    arquivo_fee_based       = diretorio / "DBV Capital_FeeBased.csv"
    arquivo_receitas        = diretorio / "DBV Capital_Receitas.csv"
    arquivo_habilitacoes    = diretorio / "DBV Capital_Habilitacoes.csv"
    arquivo_transferencias  = diretorio / "DBV Capital_Transferências.csv"
    arquivo_positivador     = diretorio / "DBV Capital_Positivador.csv"
    arquivo_diversificador  = diretorio / "DBV Capital_Diversificador.csv"
    # NOVO
    arquivo_produtos        = diretorio / "DBV Capital_Produtos.csv"
    arquivo_mesarv          = diretorio / "DBV Capital_AUC Mesa RV.csv"
    arquivo_clientes        = diretorio / "DBV Capital_Clientes.csv"
    arquivo_objetivos       = diretorio / "DBV Capital_Objetivos.csv"
    arquivo_positivador_mtd = diretorio / "DBV Capital_Positivador_MTD.csv"

    saida_fee_based       = diretorio / "DBV Capital_FeeBased.db"
    saida_receitas        = diretorio / "DBV Capital_Receitas.db"
    saida_habilitacoes    = diretorio / "DBV Capital_Habilitacoes.db"
    saida_transferencias  = diretorio / "DBV Capital_Transferências.db"
    saida_positivador     = diretorio / "DBV Capital_Positivador.db"
    saida_diversificador  = diretorio / "DBV Capital_Diversificador.db"
    # NOVO
    saida_produtos        = diretorio / "DBV Capital_Produtos.db"
    saida_mesarv          = diretorio / "DBV Capital_AUC Mesa RV.db"
    saida_clientes        = diretorio / "DBV Capital_Clientes.db"
    saida_objetivos       = diretorio / "DBV Capital_Objetivos.db"
    saida_positivador_mtd     = diretorio / "DBV Capital_Positivador_MTD.db"

    print("=== Conversor de CSV para SQLite ===\n")

    if arquivo_fee_based.exists():
        print(f"\nProcessando arquivo: {arquivo_fee_based.name}")
        importar_csv_para_sqlite(arquivo_fee_based, saida_fee_based, 'feebased')
    else:
        print(f"\nAviso: Arquivo {arquivo_fee_based.name} não encontrado.")

    if arquivo_receitas.exists():
        print(f"\nProcessando arquivo: {arquivo_receitas.name}")
        importar_csv_para_sqlite(arquivo_receitas, saida_receitas, 'receitas')
    else:
        print(f"\nAviso: Arquivo {arquivo_receitas.name} não encontrado.")

    if arquivo_habilitacoes.exists():
        print(f"\nProcessando arquivo: {arquivo_habilitacoes.name}")
        importar_csv_para_sqlite(arquivo_habilitacoes, saida_habilitacoes, 'habilitacoes')
    else:
        print(f"\nAviso: Arquivo {arquivo_habilitacoes.name} não encontrado.")

    if arquivo_transferencias.exists():
        print(f"\nProcessando arquivo: {arquivo_transferencias.name}")
        importar_csv_para_sqlite(arquivo_transferencias, saida_transferencias, 'transferencias')
    else:
        print(f"\nAviso: Arquivo {arquivo_transferencias.name} não encontrado.")

    if arquivo_positivador.exists():
        print(f"\nProcessando arquivo: {arquivo_positivador.name}")
        importar_csv_para_sqlite(arquivo_positivador, saida_positivador, 'positivador')
    else:
        print(f"\nAviso: Arquivo {arquivo_positivador.name} não encontrado.")

    if arquivo_positivador_mtd.exists():
        print(f"\nProcessando arquivo: {arquivo_positivador_mtd.name}")
        importar_csv_para_sqlite(arquivo_positivador_mtd, saida_positivador_mtd, 'positivador_mtd')
    else:
        print(f"\nAviso: Arquivo {arquivo_positivador_mtd.name} não encontrado.")

    if arquivo_diversificador.exists():
        print(f"\nProcessando arquivo: {arquivo_diversificador.name}")
        importar_csv_para_sqlite(arquivo_diversificador, saida_diversificador, 'diversificador')
    else:
        print(f"\nAviso: Arquivo {arquivo_diversificador.name} não encontrado.")

    # NOVO bloco Produtos
    if arquivo_produtos.exists():
        print(f"\nProcessando arquivo: {arquivo_produtos.name}")
        importar_csv_para_sqlite(arquivo_produtos, saida_produtos, 'produtos')
    else:
        
        print(f"\nAviso: Arquivo {arquivo_produtos.name} não encontrado.")
    
    # NOVO bloco Clientes
    if arquivo_clientes.exists():
        print(f"\nProcessando arquivo: {arquivo_clientes.name}")
        importar_csv_para_sqlite(arquivo_clientes, saida_clientes, 'clientes')
    else:
        
        print(f"\nAviso: Arquivo {arquivo_clientes.name} não encontrado.")

    # NOVO bloco MesaRV
    if arquivo_mesarv.exists():
        print(f"\nProcessando arquivo: {arquivo_mesarv.name}")
        importar_csv_para_sqlite(arquivo_mesarv, saida_mesarv, 'mesarv')
    else:
        print(f"\nAviso: Arquivo {arquivo_mesarv.name} não encontrado.")
        
    # Processar arquivo de Objetivos
    if arquivo_objetivos.exists():
        print(f"\nProcessando arquivo: {arquivo_objetivos.name}")
        importar_csv_para_sqlite(arquivo_objetivos, saida_objetivos, 'objetivos')
    else:
        print(f"\nAviso: Arquivo {arquivo_objetivos.name} não encontrado.")

    print("\nProcesso concluído!")

if __name__ == "__main__":
    main()
