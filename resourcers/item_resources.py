from flask_restful import Resource, reqparse
from models.item_models import ItemModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from bool_format import str_to_bool
import sqlite3
import os


def normalize_arguments(description=None, is_available=None, owner_id=None, limit=50, offset=0, **dados):
    """Normaliza e organiza os argumentos fornecidos para uma consulta, incluindo paginação e filtros opcionais.

    Parâmetros:
        description (str, opcional): Filtro por descrição.
        is_available (bool, opcional): Filtro para disponibilidade (True ou False).
        owner_id (int, opcional): ID do proprietário para filtro.
        limit (int, opcional): Quantidade máxima de resultados a serem retornados. Padrão é 50.
        offset (int, opcional): Quantidade de resultados a serem ignorados (para paginação). Padrão é 0.
        **dados: Argumentos adicionais não utilizados explicitamente, mas aceitos por compatibilidade.

    Retorna:
        dict: Um dicionário contendo os argumentos normalizados que foram fornecidos, incluindo 'limit' e 'offset' como padrão.""" 
    
    args = {
        "limit": limit,
        "offset": offset
    }

    if description is not None:
        args["description"] = description

    if is_available is not None:
        args["is_available"] = is_available

    if owner_id is not None:
        args["owner_id"] = owner_id

    return args


arguments = reqparse.RequestParser()
arguments.add_argument("description", type=str, location="args")
arguments.add_argument("is_available", type=str_to_bool, location="args")
arguments.add_argument("date", type=str, location="args")
arguments.add_argument("owner_id", type=int, location="args")
arguments.add_argument("limit", type=int, location="args")
arguments.add_argument("offset", type=int, location="args")



class Items(Resource):
    def get(self):
        """ Recupera itens do banco de dados com base nos parâmetros de consulta fornecidos.
    
        Essa função realiza as seguintes etapas:
        - Lê os argumentos da requisição (query string).
        - Normaliza os parâmetros utilizando a função 'normalize_arguments'.
        - Constrói dinamicamente a consulta SQL com filtros opcionais para 'description', 'is_available' e vowner_id'.
        - Aplica paginação usando 'limit' e 'offset'.
        - Executa a consulta no banco SQLite e retorna os resultados.
    
        Retorno:
            tuple: Um dicionário com a lista de itens encontrados no banco de dados e o código de status HTTP 200.
            Cada item contém os campos: 'item_id', 'description', 'is_available', 'date', 'owner_id'. """
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "instance", "data.db"))

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        args = arguments.parse_args()

        parameters = normalize_arguments(**{key: value for key, value in args.items() if value is not None})

        query = "SELECT * FROM items"
        filters = []
        values = []

        if "description" in parameters:
            filters.append("description = ?")
            values.append(parameters["description"])

        if "is_available" in parameters:
            filters.append("is_available = ?")
            values.append(int(parameters["is_available"]))

        if "owner_id" in parameters:
            filters.append("owner_id = ?")
            values.append(parameters["owner_id"])

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " LIMIT ? OFFSET ?"
        values.append(parameters["limit"]) 
        values.append(parameters["offset"]) 

        result = cursor.execute(query, tuple(values))

        items = [
            {
                "item_id": row[0],
                "description": row[1],
                "is_available": bool(row[2]),
                "date": row[3],
                "owner_id": row[4]
            }
            for row in result
        ]

        connection.close()
        return {"items": items}, 200
    


class Item(Resource):

    """Recurso da API responsável por gerenciar itens individuais.

    Esta classe define os endpoints para operações CRUD em itens com base no 'item_id'.
    Utiliza autenticação JWT para proteger operações sensíveis como criação, atualização e exclusão.

    Atributos:
        arguments (RequestParser): Define os argumentos obrigatórios para criação/atualização de itens, como
            'description' (str) e 'is_available' (bool).

    Métodos:
        get(item_id):
            Recupera um item específico pelo 'item_id'.
            Retorna o item em formato JSON se encontrado, caso contrário retorna mensagem de erro 404.

        post(item_id):
            Cria um novo item com o 'item_id' fornecido.
            Retorna erro 400 se o item já existir ou 500 em caso de erro interno.
            Requer autenticação via JWT.

        put(item_id):
            Atualiza um item existente, se encontrado e se o usuário autenticado for o proprietário.
            Retorna erro 404 se o item não existir, 403 se o usuário não for o proprietário ou 500 em caso de erro interno.
            Requer autenticação via JWT.

        delete(item_id):
            Remove um item, desde que ele exista e pertença ao usuário autenticado.
            Retorna erro 400 se o item não existir, 403 se o usuário não for o proprietário ou 500 em caso de erro interno.
            Requer autenticação via JWT."""

    arguments = reqparse.RequestParser()
    arguments.add_argument('description', type=str, required=True, help="The field 'description' can not be left blank")
    arguments.add_argument('is_available', type=bool, required=True, help="The field 'is_available' can not be left blank")


    def get(self, item_id):
        """Recupera um item específico com base no 'item_id'.

        Parâmetros:
            item_id (int): O identificador único do item a ser buscado.

        Retorno:
            dict ou tuple: Se o item for encontrado, retorna um dicionário com os dados do item em formato JSON.
            Caso contrário, retorna um dicionário com uma mensagem de erro e o código HTTP 404."""
        
        item = ItemModel.find_item(item_id)
        if item:
            return item.json()
        return {'message': 'Item not found.'}, 404 # not found
    
    
    @jwt_required()
    def post(self, item_id):
        """ Cria um novo item com o 'item_id' fornecido.

        Requer autenticação JWT para associar o item ao usuário autenticado.

        Parâmetros:
            item_id (int): O identificador único do item a ser criado.

        Retorno:
            tuple:
                - Se o item já existir, retorna uma mensagem de erro e código HTTP 400.
                - Se houver erro interno ao salvar, retorna mensagem de erro e código HTTP 500.
                - Caso criado com sucesso, retorna os dados do item em formato JSON e código HTTP 201."""
        
        if ItemModel.find_item(item_id):
            return {"message": "Item id'{}' already exists.".format(item_id)}, 400 # Bad resquest
        
        user_id = int(get_jwt_identity()) 
        data = Item.arguments.parse_args()
        item = ItemModel(item_id,**data, owner_id=user_id) 
        
        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return item.json(), 201


    @jwt_required()
    def put(self, item_id):
        """Atualiza um item existente com base no 'item_id'.

        Requer autenticação JWT e valida se o usuário autenticado é o proprietário do item.

        Parâmetros:
            item_id (int): O identificador único do item a ser atualizado.

        Retorno:
            tuple:
                - Se o item não for encontrado, retorna mensagem de erro e código HTTP 404.
                - Se o usuário não for o proprietário do item, retorna mensagem de acesso negado e código HTTP 403.
                - Se a atualização for bem-sucedida, retorna os dados atualizados do item e código HTTP 200.
                - Em caso de erro interno ao salvar, retorna mensagem de erro e código HTTP 500. """
        
        user_id = int(get_jwt_identity())
        data = Item.arguments.parse_args()
        item_finded = ItemModel.find_item(item_id)

        if not item_finded:
            return {"message": "Item not found"}, 404 #Not found

        if item_finded.owner_id != user_id:
            return {"message": "You are not allowed to update this item."}, 403 # Acess Denied

        if item_finded:
            item_finded.update_item(**data)
            return item_finded.json(), 200 #sucessful
        item = ItemModel(item_id, **data)

        try:
            item.update_item()
        except:
            return {"message": "An internal error ocurred trying to save item."}, 500 # Internal Server Error
        return item.json(), 201
    

    @jwt_required()
    def delete(self, item_id):
        """ Exclui um item com base no 'item_id'.

        Requer autenticação JWT e valida se o usuário autenticado é o proprietário do item.

        Parâmetros:
            item_id (int): O identificador único do item a ser excluído.

        Retorno:
            tuple:
                - Se o item não for encontrado, retorna mensagem de erro e código HTTP 400.
                - Se o usuário não for o proprietário do item, retorna mensagem de acesso negado e código HTTP 403.
                - Se a exclusão for bem-sucedida, retorna mensagem de sucesso e código HTTP 200 (padrão).
                - Em caso de erro interno ao excluir, retorna mensagem de erro e código HTTP 500. """
        
        user_id = int(get_jwt_identity()) 
        item = ItemModel.find_item(item_id)

        if not item:
            return {"message": "Item not found"}, 400 #Bad request

        if item.owner_id != user_id:
            return{"message": "You are not allowed to delete this item."}, 403 # Acess Denied

        try:
            item.delete_item()
            return {'message': 'Item deleted.'}
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error