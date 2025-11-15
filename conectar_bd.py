import pymysql.cursors
import os
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO DO BANCO — PRODUÇÃO + LOCAL
# =====================================================

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '1234'),
    'database': os.environ.get('DB_NAME', 'Pedidos'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# SENHA REAL — em produção vem do Render
_SENHA_REAL = os.environ.get("SENHA_REAL", "admin123")


# =====================================================
# FUNÇÃO DE CONEXÃO
# =====================================================
def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        _verificar_e_inserir_produtos_iniciais(conn)
        return conn
    except pymysql.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def _obter_senha_real():
    return _SENHA_REAL


# =====================================================
# FUNÇÕES DE PEDIDO
# =====================================================
def adicionar_itens_a_pedido_existente(conexao, cursor, pedido_id, itens_a_adicionar):
    for item in itens_a_adicionar:
        cursor.execute("""
            INSERT INTO pedido_itens
                (pedido_id, produto_id, nome_item, descricao_item, observacao_item,
                 quantidade, preco_unitario, custo_unitario, valor_item,
                 tipo_item_pedido, categoria_item_pedido, entregue, data_adicao)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, FALSE, NOW())
        """, (
            pedido_id,
            item.get('produto_id'),
            item.get('nome') or '',
            item.get('descricao') or None,
            item.get('observacao') or None,
            int(item.get('quantidade', 1)),
            float(item.get('preco_unitario') or 0.0),
            float(item.get('custo_unitario') or 0.0),
            round(float(item.get('preco_unitario') or 0) * int(item.get('quantidade', 1)), 2),
            item.get('tipo') or None,
            item.get('categoria') or None
        ))
    conexao.commit()


def fechar_pedido(conexao, cursor, comanda_id, forma_pagamento, observacao_pagamento):
    cursor.execute("SELECT id FROM pedidos WHERE comanda_id=%s AND situacao='ABERTO'", (comanda_id,))
    pedido = cursor.fetchone()
    if pedido:
        cursor.execute("""
            UPDATE pedidos
            SET situacao='FECHADO',
                data_fechamento=%s,
                forma_pagamento=%s,
                observacao_pagamento=%s
            WHERE id=%s
        """, (datetime.now(), forma_pagamento, observacao_pagamento, pedido['id']))
        conexao.commit()
        return pedido['id']
    return None


def cancelar_pedido(conexao, cursor, comanda_id):
    cursor.execute("DELETE FROM pedidos WHERE comanda_id=%s AND situacao='ABERTO'", (comanda_id,))
    afetado = cursor.rowcount
    conexao.commit()
    return afetado > 0


# =====================================================
# INSERÇÃO DE PRODUTOS FIXOS
# =====================================================
def _verificar_e_inserir_produtos_iniciais(conn):
    cursor = conn.cursor()

    # Prato Dinâmico
    cursor.execute("SELECT id FROM produtos WHERE nome='Prato' AND tipo='Prato_Dinamico'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO produtos (nome, preco, custo, tipo, categoria)
            VALUES ('Prato', 0, 5, 'Prato_Dinamico', 'Refeição')
        """)
        conn.commit()

    # Sobremesa Dinâmica
    cursor.execute("SELECT id FROM produtos WHERE nome='Sobremesa' AND tipo='Sobremesa_Dinamica'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO produtos (nome, preco, custo, tipo, categoria)
            VALUES ('Sobremesa', 0, 0, 'Sobremesa_Dinamica', 'Doce/Sorvete')
        """)
        conn.commit()

    # Item Variado
    cursor.execute("SELECT id FROM produtos WHERE nome='Item Variado' AND tipo='Item_Variado_Dinamico'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO produtos (nome, preco, custo, tipo, categoria)
            VALUES ('Item Variado', 0, 0, 'Item_Variado_Dinamico', 'Outros')
        """)
        conn.commit()

    # Produtos comuns
    produtos_fixos = [
        ('Marmita P', 22, 8, 'Marmita_P', 'Refeição'),
        ('Marmita Teste', 0.01, 0.01, 'Marmita_P', 'Refeição'),
        ('Marmita M', 23.50, 10, 'Marmita_M', 'Refeição'),
        ('Marmita G', 27, 12, 'Marmita_G', 'Refeição'),
        ('Marmita Econômica', 13.99, 6, 'Marmita_Economica', 'Refeição'),

        # Refrigerantes
        ('Coca-Cola 600ml', 7, 4.50, 'Refrigerante', 'Bebida'),
        ('Refrigerante 600ml', 7, 4.50, 'Refrigerante', 'Bebida'),
        ('Coca-Cola KS', 5, 2, 'Refrigerante', 'Bebida'),
        ('Coca-Cola KS Zero', 5, 2, 'Refrigerante', 'Bebida'),
        ('Coca-Cola Lata', 6, 3.05, 'Refrigerante', 'Bebida'),
        ('Lata (Outras)', 6, 3.05, 'Refrigerante', 'Bebida'),
        ('Caçulinha', 2.50, 1.55, 'Refrigerante', 'Bebida'),
        ('Esportiva', 6, 2.69, 'Refrigerante', 'Bebida'),
        ('Coca-Cola 2L', 15, 9.94, 'Refrigerante', 'Bebida'),
        ('Coca-Cola 1L', 10, 4.30, 'Refrigerante', 'Bebida'),
        ('Festa 2L', 6, 3.50, 'Refrigerante', 'Bebida'),
        ('Itubaina KS', 6, 3.50, 'Refrigerante', 'Bebida'),

        # Sucos
        ('Suco Del Valle', 6, 3.29, 'Suco', 'Bebida'),
        ('Suco', 8, 3, 'Suco', 'Bebida'),
        ('Suco Peq Limão', 5, 2, 'Suco', 'Bebida'),
        ('Suco Peq Laranja', 5, 2, 'Suco', 'Bebida'),
        ('Suco de Laranja', 10, 4, 'Suco', 'Bebida'),
        ('Jarra de Suco', 18, 7, 'Suco', 'Bebida'),
    ]

    # Prefeitura
    cursor.execute("SELECT id FROM produtos WHERE nome='Prefeitura'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO produtos (nome, preco, custo, tipo, categoria)
            VALUES ('Prefeitura', 28, 0, 'Prefeitura', 'Refeição')
        """)
        conn.commit()

    # Inserir produtos fixos
    for nome, preco, custo, tipo, categoria in produtos_fixos:
        cursor.execute("SELECT id FROM produtos WHERE nome=%s", (nome,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO produtos (nome, preco, custo, tipo, categoria)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, preco, custo, tipo, categoria))
            conn.commit()

    cursor.close()
