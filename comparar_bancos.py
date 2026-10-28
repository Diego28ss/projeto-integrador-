import sqlite3
import os

# Caminhos absolutos dos dois bancos de dados
db1_path = r"C:\Users\adm\Documents\mypj\projeto-integrador-\dados\jb_tintas.db"
db2_path = r"C:\Users\adm\Documents\mypj\projeto-integrador-\jb_tintas.db"

def obter_estrutura_banco(caminho_db):
    if not os.path.exists(caminho_db):
        return None
    
    conexao = sqlite3.connect(caminho_db)
    cursor = conexao.cursor()
    
    # Pega todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [linha[0] for linha in cursor.fetchall()]
    
    estrutura = {}
    for tabela in tabelas:
        # Pega as colunas de cada tabela
        cursor.execute(f"PRAGMA table_info({tabela});")
        colunas = [linha[1] for linha in cursor.fetchall()]
        estrutura[tabela] = set(colunas)
        
    conexao.close()
    return estrutura

print("="*60)
print("🔍 INICIANDO AUDITORIA DOS BANCOS DE DADOS...")
print("="*60)

estrutura_db1 = obter_estrutura_banco(db1_path)
estrutura_db2 = obter_estrutura_banco(db2_path)

if estrutura_db1 is None:
    print(f"❌ ERRO: Banco não encontrado em: {db1_path}")
if estrutura_db2 is None:
    print(f"❌ ERRO: Banco não encontrado em: {db2_path}")

if estrutura_db1 and estrutura_db2:
    tabelas_db1 = set(estrutura_db1.keys())
    tabelas_db2 = set(estrutura_db2.keys())
    
    # 1. Compara as Tabelas
    tabelas_so_no_db1 = tabelas_db1 - tabelas_db2
    tabelas_so_no_db2 = tabelas_db2 - tabelas_db1
    tabelas_comuns = tabelas_db1.intersection(tabelas_db2)
    
    print("\n📊 COMPARAÇÃO DE TABELAS:")
    if not tabelas_so_no_db1 and not tabelas_so_no_db2:
        print("✅ Os dois bancos possuem EXATAMENTE as mesmas tabelas.")
    else:
        if tabelas_so_no_db1:
            print(f"⚠️ Tabelas APENAS no banco da pasta 'dados': {', '.join(tabelas_so_no_db1)}")
        if tabelas_so_no_db2:
            print(f"⚠️ Tabelas APENAS no banco da raiz: {', '.join(tabelas_so_no_db2)}")
            
    # 2. Compara as Colunas das tabelas comuns
    print("\n🧬 COMPARAÇÃO DE COLUNAS (Nas tabelas comuns):")
    diferencas_colunas = False
    
    for tabela in tabelas_comuns:
        colunas_db1 = estrutura_db1[tabela]
        colunas_db2 = estrutura_db2[tabela]
        
        if colunas_db1 != colunas_db2:
            diferencas_colunas = True
            col_so_db1 = colunas_db1 - colunas_db2
            col_so_db2 = colunas_db2 - colunas_db1
            print(f"\n❌ Diferença na tabela '{tabela}':")
            if col_so_db1:
                print(f"   -> Colunas só na pasta 'dados': {', '.join(col_so_db1)}")
            if col_so_db2:
                print(f"   -> Colunas só na raiz: {', '.join(col_so_db2)}")
                
    if not diferencas_colunas:
        print("✅ Todas as tabelas comuns possuem EXATAMENTE as mesmas colunas.")
        
    if not tabelas_so_no_db1 and not tabelas_so_no_db2 and not diferencas_colunas:
        print("\n🏆 RESULTADO FINAL: Os dois bancos de dados são 100% IDÊNTICOS em estrutura!")
    else:
        print("\n⚠️ RESULTADO FINAL: Existem divergências estruturais entre os bancos.")
        