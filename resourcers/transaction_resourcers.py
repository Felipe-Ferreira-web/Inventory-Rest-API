from flask_restful import Resource, reqparse
from models.transaction_models import TransactionModel
from models.item_models import ItemModel
from  flask_jwt_extended import jwt_required, get_jwt_identity
from bool_format import str_to_bool
import sqlite3
import os


def normalize_arguments(transaction_id=None, item_id=None, from_user_id=None, to_user_id=None, is_available=None, limit=100, offset=0, **dados):
    """Normaliza e organiza os argumentos fornecidos para uma consulta de transações, incluindo filtros e paginação.

    Parâmetros:
        transaction_id (int, opcional): Filtro pelo ID da transação.
        item_id (int, opcional): Filtro pelo ID do item relacionado à transação.
        from_user_id (int, opcional): Filtro pelo ID do usuário que iniciou a transação.
        to_user_id (int, opcional): Filtro pelo ID do usuário que recebeu a transação.
        is_available (bool, opcional): Filtro para disponibilidade do item relacionado.
        limit (float, opcional): Quantidade máxima de resultados retornados. Padrão é 100.
        offset (float, opcional): Quantidade de resultados a serem ignorados (para paginação). Padrão é 0.
        **dados: Argumentos adicionais não utilizados explicitamente, mas aceitos para compatibilidade.

    Retorno:
        dict: Um dicionário contendo os argumentos normalizados que foram fornecidos, incluindo 'limit' e 'offset' como padrão."""
    
    args = {
        "limit": limit,
        "offset": offset
    }

    if transaction_id is not None:
        args["transaction_id"] = transaction_id

    if item_id is not None:
        args["item_id"] = item_id

    if from_user_id is not None:
        args["from_user_id"] = from_user_id

    if to_user_id is not None:
        args["to_user_id"] = to_user_id

    if is_available is not None:
        args["is_available"] = is_available

    return args

    
arguments = reqparse.RequestParser()
arguments.add_argument("transaction_id", type=int, location="args")
arguments.add_argument("item_id", type=int, location="args")
arguments.add_argument("from_user_id", type=int, location="args")
arguments.add_argument("to_user_id", type=int, location="args")
arguments.add_argument("is_available", type=str_to_bool, location="args")
arguments.add_argument("date", type=str, location="args")
arguments.add_argument("limit", type=float, location="args")
arguments.add_argument("offset", type=float, location="args")



class Transactions(Resource):
    def get(self):
        """ Recupera transações do banco de dados com base nos parâmetros de consulta fornecidos.

        Esta função:
        - Lê os argumentos da requisição (query string).
        - Normaliza os parâmetros utilizando a função 'normalize_arguments'.
        - Constrói dinamicamente a consulta SQL com filtros opcionais para 'transaction_id', 'item_id', 'from_user_id', 'to_user_id' e 'is_available'.
        - Aplica paginação usando 'limit' e 'offset'.
        - Executa a consulta no banco SQLite e retorna os resultados.

        Retorno:
            tuple: Um dicionário contendo a lista de transações encontradas e o código de status HTTP 200.
                   Cada transação contém os campos: 'transaction_id', 'item_id', 'from_user_id', 'to_user_id', 'is_available' e 'date'. """

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "instance", "data.db"))
    
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        args = arguments.parse_args()

        parameters = normalize_arguments(**{key: value for key, value in args.items() if value is not None})

        query = "SELECT * FROM transactions"
        filters = []
        values = []

        if "transaction_id" in parameters:
            filters.append("transaction_id = ?")
            values.append(parameters["transaction_id"])

        if "item_id" in parameters:
            filters.append("item_id = ?")
            values.append(parameters["item_id"])

        if "from_user_id" in parameters:
            filters.append("from_user_id = ?")
            values.append(parameters["from_user_id"])

        if "to_user_id" in parameters:
            filters.append("to_user_id = ?")
            values.append(parameters["to_user_id"])

        if "is_available" in parameters:
            filters.append("is_available = ?")
            values.append(int(parameters["is_available"]))
        
        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " LIMIT ? OFFSET ?"
        values.append(parameters["limit"]) 
        values.append(parameters["offset"]) 

        result = cursor.execute(query, tuple(values))

        transactions = [
            {
                "transaction_id": row[0],
                "item_id": row[1],
                "from_user_id": row[2],
                "to_user_id": row[3],
                "is_available": bool(row[4]),
                "date": row[5]
            }
            for row in result
        ]

        connection.close()
        return {"transactions": transactions}, 200
    


class LoanTransaction(Resource):
    """ Recurso para realizar o empréstimo de um item de um usuário para outro.

        Método POST:
            Realiza a transferência de um item de seu dono original para o usuário autenticado,
            registrando a transação e atualizando o status de disponibilidade do item. """
    

    @jwt_required()
    def post(self):
        """ Realiza o empréstimo de um item.

            - Valida se o item existe.
            - Verifica se o usuário autenticado não é o dono do item.
            - Confirma se o item está disponível para transferência.
            - Atualiza o status do item para indisponível.
            - Registra a transação de empréstimo.

            Retorno:
                tuple:
                    - Se o item não for encontrado, retorna mensagem e código HTTP 404.
                    - Se o usuário já for o dono do item, retorna mensagem e código HTTP 400.
                    - Se o item não estiver disponível, retorna mensagem e código HTTP 403.
                    - Se houver erro interno ao salvar, retorna mensagem e código HTTP 500.
                    - Se sucesso, retorna os dados da transação e código HTTP 201. """ 

        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        data = arguments.parse_args()
        item_id = data['item_id']
        user_id = int(get_jwt_identity())

        item = ItemModel.query.get(item_id)

        if not item:                                        
            return {"message": "item not found."}, 404
        
        if item.owner_id == user_id:                       
            return {"message": "This item is already in your inventory"}, 400
        
        if item.is_available != True:
            return{"message": "Item is not available for transfer."}, 403
        
        item.is_available = False

        transaction = TransactionModel(
            item_id = item_id,
            from_user_id = item.owner_id,
            to_user_id = user_id,
            is_available = item.is_available)

        try:
            transaction.save_transaction()
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error}
        return transaction.json(), 201
    
    

class DevolutionTransaction(Resource):
    """ Recurso para registrar a devolução de um item emprestado a um usuário.

        Método POST:
            Realiza a devolução de um item pelo usuário que o recebeu,
            atualizando o status do item e registrando a transação de devolução. """
    

    @jwt_required()
    def post(self):
        """ Realiza a devolução de um item emprestado.

            - Valida se o item existe.
            - Obtém a última transação de empréstimo do item.
            - Verifica se o usuário autenticado é o atual detentor do item.
            - Atualiza o status do item para disponível.
            - Registra a transação de devolução.

            Retorno:
                tuple:
                    - Se o item não for encontrado, retorna mensagem e código HTTP 404.
                    - Se não houver transação prévia, retorna mensagem e código HTTP 404.
                    - Se o usuário autenticado não estiver com o item, retorna mensagem e código HTTP 403.
                    - Se houver erro interno ao salvar, retorna mensagem e código HTTP 500.
                    - Se sucesso, retorna os dados da transação e código HTTP 201. """
        
        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        data = arguments.parse_args()

        item_id = data['item_id']
        user_id = int(get_jwt_identity())
        item = ItemModel.query.get(item_id)

        if not item:                                        
            return {"message": "item not found."}, 404
        
        loan = TransactionModel.query.filter_by(item_id=item_id).order_by(TransactionModel.transaction_id.desc()).first()

        if not loan:
            return {"message": "No transaction was made"}, 404

        if loan.to_user_id != user_id:
            return{"message": "This item is not in your inventory"}, 403
        
        item.is_available = True

        transaction = TransactionModel(
            item_id = item_id,
            from_user_id = user_id,
            to_user_id = loan.from_user_id,
            is_available = item.is_available)
        
        try:
            transaction.save_transaction()
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return transaction.json(), 201
