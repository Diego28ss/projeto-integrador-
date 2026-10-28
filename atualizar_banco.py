import sqlite3

# Caminho do banco que precisa ser atualizado
db_dados = r"C:\Users\adm\Documents\mypj\projeto-integrador-\dados\jb_tintas.db"

# Comandos SQL para criar as colunas exatas que faltam
novas_colunas = [
    "ALTER TABLE inventario_produtos ADD COLUMN cod_interno varchar(50) NULL;",
    "ALTER TABLE inventario_produtos ADD COLUMN cod_fornecedor varchar(50) NULL;",
    "ALTER TABLE inventario_produtos ADD COLUMN ncm varchar(20) NULL;",
    "ALTER TABLE inventario_produtos ADD COLUMN cest varchar(20) NULL;",
    "ALTER TABLE inventario_produtos ADD COLUMN cfop_padrao_id bigint NULL REFERENCES inventario_tributacaocfop(id);",
    "ALTER TABLE inventario_produtos ADD COLUMN csosn_padrao_id bigint NULL REFERENCES inventario_tributacaocsosn(id);"
]

conexao = sqlite3.connect(db_dados)
cursor = conexao.cursor()

print("="*50)
print("🛠️ INJETANDO COLUNAS NO BANCO 'DADOS'...")
print("="*50)

for query in novas_colunas:
    coluna_nome = query.split('ADD COLUMN ')[1].split(' ')[0]
    try:
        cursor.execute(query)
        print(f"✅ Coluna '{coluna_nome}' adicionada com sucesso!")
    except Exception as e:
        print(f"⚠️ Aviso na coluna '{coluna_nome}': {e}")

conexao.commit()
conexao.close()

print("\n🚀 Operação concluída! O banco está atualizado.")
