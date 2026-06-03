import sqlite3

try:
    conexao = sqlite3.connect('cmms_industrial.db')
    cursor = conexao.cursor()
    
    # EM VEZ DE DELETAR, NÓS ATUALIZAMOS (UPDATE):
    # Transforma o texto vazio '' no valor oficial de vazio do banco de dados (NULL)
    cursor.execute("UPDATE itens_por_molde SET id_referencia_molde = NULL WHERE id_referencia_molde = ''")
    
    # Se por acaso houver algum salvo como a palavra 'null' em texto, ajusta também
    cursor.execute("UPDATE itens_por_molde SET id_referencia_molde = NULL WHERE id_referencia_molde = 'null'")
    
    conexao.commit()
    
    print("✅ Sucesso! Os itens sem molde foram preservados e agora o banco reconhece o vazio corretamente (NULL).")

except Exception as e:
    print(f"❌ Ocorreu um erro: {e}")

finally:
    conexao.close()