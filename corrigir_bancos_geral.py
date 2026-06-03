import os
import sqlite3

# 1. Procura todos os arquivos que terminam com .db ou .sqlite3 na raiz
arquivos_banco = [f for f in os.listdir('.') if f.endswith('.db') or f.endswith('.sqlite3')]

print("====================================================")
print(f"Arquivos de banco de dados detectados: {arquivos_banco}")
print("====================================================\n")

if not arquivos_banco:
    print("❌ Nenhum arquivo de banco (.db ou .sqlite3) encontrado na raiz do projeto.")

for banco in arquivos_banco:
    caminho_absoluto = os.path.abspath(banco)
    print(f"Checking: {banco} em ({caminho_absoluto})")
    
    try:
        conn = sqlite3.connect(banco)
        cursor = conn.cursor()
        
        # Tenta criar a coluna status
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN status TEXT;")
        conn.commit()
        print(f"  ✅ Coluna 'status' injetada com sucesso.")
        
        # Preenche todo mundo como Ativo
        cursor.execute("UPDATE colaboradores SET status = 'Ativo';")
        conn.commit()
        print(f"  ✅ Todos os colaboradores marcados como 'Ativo'.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  ℹ️ Este arquivo já tinha a coluna 'status'. Forçando atualização dos dados...")
            try:
                cursor.execute("UPDATE colaboradores SET status = 'Ativo';")
                conn.commit()
                print("  ✅ Dados sincronizados como 'Ativo'.")
            except Exception as err:
                print(f"  ❌ Erro ao atualizar dados: {err}")
        else:
            print(f"  ❌ Erro no SQLite: {e}")
    except Exception as e:
        print(f"  ❌ Erro inesperado: {e}")
    finally:
        conn.close()
        print("-" * 50)

print("\n🚀 Processo concluído! Reinicie o servidor do Django.")