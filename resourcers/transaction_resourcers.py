from flask_restful import Resource, reqparse
from models.transaction_models import TransactionModel
from models.item_models import ItemModel
from  flask_jwt_extended import jwt_required, get_jwt_identity
from bool_format import str_to_bool
import sqlite3
import os

# Normaliza e filtra os argumentos de entrada utilizados para montar consultas ao banco de dados
def normalize_arguments(transaction_id=None, item_id=None, from_user_id=None, to_user_id=None, is_available=None, limit=100, offset=0, **dados):

    # Inicicializa dicionário com os argumentos obrigatórios de paginação
    args = {
        "limit": limit,
        "offset": offset
    }

    # Adiciona transacition_id se fornecido
    if transaction_id is not None:
        args["transaction_id"] = transaction_id

    # Adiciona item_id se fornecido
    if item_id is not None:
        args["item_id"] = item_id

    # Adiciona from_user_id se fornecido
    if from_user_id is not None:
        args["from_user_id"] = from_user_id

    # Adiciona to_user_id se fornecido
    if to_user_id is not None:
        args["to_user_id"] = to_user_id

    # Adiciona is_available se fornecido
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

# classe para busca e filtragem de transações
class Transactions(Resource):
    def get(self):
        
        # Pega o diretório base do arquivo atual
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Monta o caminha completo até o banco
        DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "instance", "data.db"))
    
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        args = arguments.parse_args()

        # Filtra os argumentos, removendo os que estão como None, e normaliza para uso
        parameters = normalize_arguments(**{key: value for key, value in args.items() if value is not None})

        query = "SELECT * FROM transactions"  # Inicia a query base para selecionar todas as transações
        filters = []
        values = []

        # Adiciona filtro para transaction_id, se fornecido
        if "transaction_id" in parameters:
            filters.append("transaction_id = ?")
            values.append(parameters["transaction_id"])

        # Adiciona filtro para item_id, se fornecido
        if "item_id" in parameters:
            filters.append("item_id = ?")
            values.append(parameters["item_id"])

        # Adiciona filtro para from_user_id, se fornecido
        if "from_user_id" in parameters:
            filters.append("from_user_id = ?")
            values.append(parameters["from_user_id"])

        # Adiciona filtro para to_user_id, se fornecido
        if "to_user_id" in parameters:
            filters.append("to_user_id = ?")
            values.append(parameters["to_user_id"])

        # Adiciona filtro para is_available, convertendo para int (0 ou 1)
        if "is_available" in parameters:
            filters.append("is_available = ?")
            values.append(int(parameters["is_available"]))
        
        # Se houver filtros adicionados, irá concatenalos na cláusula WHERE
        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " LIMIT ? OFFSET ?"
        values.append(parameters["limit"]) # Define o limite de registros
        values.append(parameters["offset"]) # Define de quantos em quantos registros serão pulados

        result = cursor.execute(query, tuple(values))

        # Constrói uma lista de dicionários com os dados de cada transação encontrada
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
    
# classe para criação de empréstimo 
class LoanTransaction(Resource):

    @jwt_required()
    def post(self):
        
        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        data = arguments.parse_args()


        item_id = data['item_id'] # valor que o usuario inseriu
        user_id = int(get_jwt_identity()) # id do usuario logado

        # Pega o item no banco ItemModel
        item = ItemModel.query.get(item_id)

        # Se o item existe
        if not item:                                        
            return {"message": "item not found."}, 404
        
        # Se o item já não está no inventario de quem fez a requisição
        if item.owner_id == user_id:                       
            return {"message": "This item is already in your inventory"}, 400
        

        # Se o item está disponivel
        if item.is_available != True:
            return{"message": "Item is not available for transfer."}, 403
        
        # Altera o status de is_available para indisponivel(False)
        item.is_available = False

        # Faz a transação
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
    
    
# classe para criação de devolução
class DevolutionTransaction(Resource):
    
    @jwt_required()
    def post(self):
        
        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        data = arguments.parse_args()

        item_id = data['item_id'] # valor que o usuario inseriu
        user_id = int(get_jwt_identity())# id do usuario logado

        # Pega o item no banco ItemModel
        item = ItemModel.query.get(item_id)

        # Se o item existe
        if not item:                                        
            return {"message": "item not found."}, 404
        
        # Pega o id da ultima transação feita com o item
        loan = TransactionModel.query.filter_by(item_id=item_id).order_by(TransactionModel.transaction_id.desc()).first()

        # Checa se o user está com o item
        if not loan:
            return {"message": "No transaction was made"}, 404

        # Checa se quem está fazendo a devolução é quem fez o empréstimo
        if loan.to_user_id != user_id:
            return{"message": "This item is not in your inventory"}, 403
        
        # Como o item foi devolvido, ele volta para o status de disponibilidade padrão (True)
        item.is_available = True

        # Cria uma transação de devolução
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
