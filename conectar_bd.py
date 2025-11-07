import pymysql.cursors
from datetime import datetime

# Configurações do Banco de Dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # SEU USUÁRIO DO MYSQL AQUI!
    'password': '91130120605', # SUA SENHA DO MYSQL AQUI!
    'database': 'pedidos',     # Nome do seu banco de dados é 'Pedidos'
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor # Isso faz com que cursor() retorne dicionários por padrão
}

# Senha para operações sensíveis (MUITO IMPORTANTE: Em produção, NUNCA hardcode isso!)
_SENHA_REAL = "admin123" # TROQUE POR UMA SENHA SEGURA!

def get_db_connection():
    """Tenta conectar ao banco de dados e retorna a conexão."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        # Garante que os produtos iniciais existam ao iniciar a conexão (ou no primeiro uso)
        # Atenção: Isso pode ser chamado muitas vezes, considere chamar uma única vez na inicialização do Flask
        _verificar_e_inserir_produtos_iniciais(conn)
        return conn
    except pymysql.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def _obter_senha_real():
    """Retorna a senha para validação."""
    return _SENHA_REAL

def adicionar_itens_a_pedido_existente(conexao, cursor, pedido_id, itens_a_adicionar):
    """
    Insere os itens em pedido_itens. Espera que cada item seja dict com chaves:
    produto_id, nome, descricao, quantidade, preco_unitario, custo_unitario, tipo, categoria, observacao
    """
    for item in itens_a_adicionar:
        produto_id = item.get('produto_id')
        nome_item = item.get('nome') or ''
        descricao = item.get('descricao') or None
        observacao = item.get('observacao') or None
        quantidade = int(item.get('quantidade', 1))
        preco_unitario = float(item.get('preco_unitario') or 0.0)
        custo_unitario = float(item.get('custo_unitario') or 0.0)
        tipo_item = item.get('tipo') or None
        categoria_item = item.get('categoria') or None
        valor_item = round(preco_unitario * quantidade, 2)

        cursor.execute("""
            INSERT INTO pedido_itens
                (pedido_id, produto_id, nome_item, descricao_item, observacao_item,
                 quantidade, preco_unitario, custo_unitario, valor_item, tipo_item_pedido, categoria_item_pedido, entregue, data_adicao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NOW())
        """, (
            pedido_id,
            produto_id,
            nome_item,
            descricao,
            observacao,
            quantidade,
            preco_unitario,
            custo_unitario,
            valor_item,
            tipo_item,
            categoria_item
        ))
    conexao.commit()

def fechar_pedido(conexao, cursor, comanda_id, forma_pagamento, observacao_pagamento):
    """
    Fecha um pedido existente.
    Retorna o ID do pedido se fechado com sucesso, ou None se não encontrado.
    """
    try:
        cursor.execute("SELECT id FROM pedidos WHERE comanda_id = %s AND situacao = 'ABERTO'", (comanda_id,))
        pedido = cursor.fetchone()
        if pedido:
            pedido_id = pedido['id']
            cursor.execute(
                "UPDATE pedidos SET situacao = 'FECHADO', data_fechamento = %s, forma_pagamento = %s, observacao_pagamento = %s WHERE id = %s",
                (datetime.now(), forma_pagamento, observacao_pagamento, pedido_id)
            )
            conexao.commit()
            return pedido_id
        return None
    except pymysql.Error as e:
        conexao.rollback()
        print(f"Erro ao fechar pedido: {e}")
        raise # Re-levanta a exceção
    except Exception as e:
        conexao.rollback()
        print(f"Erro inesperado ao fechar pedido: {e}")
        raise

def cancelar_pedido(conexao, cursor, comanda_id):
    """
    Cancela e exclui um pedido.
    Retorna True se cancelado/excluído com sucesso, False se não encontrado.
    """
    try:
        # A trigger ON DELETE CASCADE na tabela pedido_itens cuidará dos itens.
        cursor.execute("DELETE FROM pedidos WHERE comanda_id = %s AND situacao = 'ABERTO'", (comanda_id,))
        afetado = cursor.rowcount
        conexao.commit()
        return afetado > 0
    except pymysql.Error as e:
        conexao.rollback()
        print(f"Erro ao cancelar pedido: {e}")
        raise
    except Exception as e:
        conexao.rollback()
        print(f"Erro inesperado ao cancelar pedido: {e}")
        raise


def _verificar_e_inserir_produtos_iniciais(conn):
    """
    Verifica se os produtos iniciais existem e os insere se não existirem.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        # Verificar e inserir Prato Dinâmico
        cursor.execute("SELECT id FROM produtos WHERE nome = 'Prato' AND tipo = 'Prato_Dinamico'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO produtos (nome, preco, custo, tipo, categoria) VALUES (%s, %s, %s, %s, %s)",
                           ('Prato', 0.00, 5.00, 'Prato_Dinamico', 'Refeição'))
            conn.commit()
            print("Produto 'Prato' (Prato_Dinamico) inserido ou verificado.")

        # Verificar e inserir Sobremesa Dinâmica
        cursor.execute("SELECT id FROM produtos WHERE nome = 'Sobremesa' AND tipo = 'Sobremesa_Dinamica'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO produtos (nome, preco, custo, tipo, categoria) VALUES (%s, %s, %s, %s, %s)",
                           ('Sobremesa', 0.00, 0.00, 'Sobremesa_Dinamica', 'Doce/Sorvete'))
            conn.commit()
            print("Produto 'Sobremesa' (Sobremesa_Dinamica) inserido ou verificado.")
            
        # Verificar e inserir Item Variado Dinâmico (se ainda não existir)
        cursor.execute("SELECT id FROM produtos WHERE nome = 'Item Variado' AND tipo = 'Item_Variado_Dinamico'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO produtos (nome, preco, custo, tipo, categoria) VALUES (%s, %s, %s, %s, %s)",
                           ('Item Variado', 0.00, 0.00, 'Item_Variado_Dinamico', 'Outros'))
            conn.commit()
            print("Produto 'Item Variado' (Item_Variado_Dinamico) inserido ou verificado.")

        # Produtos fixos
        produtos_fixos = [
            ('Marmita P', 22.00, 8.00, 'Marmita_P', 'Refeição'),
            ('Marmita Teste', 0.01, 0.01, 'Marmita_P', 'Refeição'),
            ('Marmita M', 23.50, 10.00, 'Marmita_M', 'Refeição'),
            ('Marmita G', 27.00, 12.00, 'Marmita_G', 'Refeição'),
            ('Marmita Econômica', 13.99, 6.00, 'Marmita_Economica', 'Refeição'), # Adicionado Marmita Econômica
            ('Coca-Cola 600ml', 7.00, 4.50, 'Bebida', 'Bebida'),
            ('Refrigerante 600ml', 7.00, 4.50, 'Bebida', 'Bebida'),
            ('Coca-Cola KS', 5.00, 2.00, 'Bebida', 'Bebida'),
            ('TESTE', 0.1, 0.1, 'Bebida', 'Bebida'),
            ('Coca-Cola KS Zero', 5.00, 2.00, 'Bebida', 'Bebida'),
            ('Coca-Cola Lata', 6.00, 3.05, 'Bebida', 'Bebida'),
            ('Lata (Outras)', 6.00, 3.05, 'Bebida', 'Bebida'),
            ('Caçulinha', 2.50, 1.55, 'Bebida', 'Bebida'),
            ('Água com Gás', 4.00, 1.55, 'Bebida', 'Bebida'),
            ('Água sem Gás', 4.00, 1.38, 'Bebida', 'Bebida'),
            ('Esportiva', 6.00, 2.69, 'Bebida', 'Bebida'),
            ('Coca-Cola 2L', 15.00, 9.94, 'Bebida', 'Bebida'),
            ('Coca-Cola 1L', 10.00, 4.30, 'Bebida', 'Bebida'),
            ('Festa 2L', 6.00, 3.50, 'Bebida', 'Bebida'),
            ('Itubaina KS', 6.00, 3.50, 'Bebida', 'Bebida'),
            ('Suco Del Valle', 6.00, 3.29, 'Bebida', 'Bebida'),
            ('Suco', 8.00, 3.00, 'Bebida', 'Bebida'),
            ('Suco Peq Limão', 5.00, 2.00, 'Bebida', 'Bebida'),
            ('Suco Peq Laranja', 5.00, 2.00, 'Bebida', 'Bebida'),
            ('Suco de Laranja', 10.00, 4.00, 'Bebida', 'Bebida'),
            ('Jarra de Suco', 18.00, 7.00, 'Bebida', 'Bebida'),

        ]
        
        # Produto fixo Prefeitura
        cursor.execute("SELECT id FROM produtos WHERE nome = 'Prefeitura'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO produtos (nome, preco, custo, tipo, categoria)
                VALUES (%s, %s, %s, %s, %s)
            """, ('Prefeitura', 28.00, 0.00, 'Prefeitura', 'Refeição'))
            conn.commit()
            print("Produto 'Prefeitura' inserido ou verificado.")


        for nome, preco, custo, tipo, categoria in produtos_fixos:
            cursor.execute("SELECT id FROM produtos WHERE nome = %s", (nome,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO produtos (nome, preco, custo, tipo, categoria) VALUES (%s, %s, %s, %s, %s)",
                               (nome, preco, custo, tipo, categoria))
                conn.commit()
                print(f"Produto '{nome}' inserido.")
    except pymysql.Error as err:
        print(f"Erro ao verificar/inserir produtos iniciais: {err}")
    finally:
        if cursor:
            cursor.close()