from flask_restful import Resource, reqparse
from models.item_models import ItemModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from bool_format import bool_to_str
import sqlite3
import os

# Normaliza e filtra os argumentos de entrada utilizados para montar consultas ao banco de dados
def normalize_arguments(description=None, is_available=None, owner_id=None, limit=50, offset=0, **dados):

    # Inicicializa dicionário com os argumentos obrigatórios de paginação
    args = {
        "limit": limit,
        "offset": offset
    }

    # Adiciona description se fornecido
    if description is not None:
        args["description"] = description

    # Adiciona os_available se fornecido
    if is_available is not None:
        args["is_available"] = is_available

    # Adiciona owner_id se fornecido
    if owner_id is not None:
        args["owner_id"] = owner_id

    return args


arguments = reqparse.RequestParser()
arguments.add_argument("description", type=str, location="args")
arguments.add_argument("is_available", type=bool_to_str, location="args")
arguments.add_argument("date", type=str, location="args")
arguments.add_argument("owner_id", type=int, location="args")
arguments.add_argument("limit", type=int, location="args")
arguments.add_argument("offset", type=int, location="args")

# classe para busca e filgragem de items
class Items(Resource):
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

        query = "SELECT * FROM items"
        filters = []
        values = []

        # Adiciona filtro para description, se fornecido
        if "description" in parameters:
            filters.append("description = ?")
            values.append(parameters["description"])

        # Adiciona filtro para is_available, se fornecido
        if "is_available" in parameters:
            filters.append("is_available = ?")
            values.append(int(parameters["is_available"]))

        # Adiciona filtro para owner_id, se fornecido
        if "owner_id" in parameters:
            filters.append("owner_id = ?")
            values.append(parameters["owner_id"])

        # Se houver filtros adicionados, irá concatenalos na cláusula WHERE
        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " LIMIT ? OFFSET ?"
        values.append(parameters["limit"]) # Define o limite de registros
        values.append(parameters["offset"]) # Define de quantos em quantos registros serão pulados

        result = cursor.execute(query, tuple(values))

        # Constrói uma lista de dicionários com os dados de cada transação encontrada
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
    

# (Item) classe para manipulação de items
class Item(Resource):
    arguments = reqparse.RequestParser()
    arguments.add_argument('description', type=str, required=True, help="The field 'description' can not be left blank")
    arguments.add_argument('is_available', type=bool, required=True, help="The field 'is_available' can not be left blank")

    # Pega o item pelo item_id
    def get(self, item_id):
        item = ItemModel.find_item(item_id)
        if item:
            return item.json()
        return {'message': 'Item not found.'}, 404 # not found
    

    # Insere os valores inseridos do item no banco
    @jwt_required()
    def post(self, item_id):
        if ItemModel.find_item(item_id):
            return {"message": "Item id'{}' already exists.".format(item_id)}, 400 # Bad resquest
        
        user_id = int(get_jwt_identity()) # Pega o id do user logado
        data = Item.arguments.parse_args()
        item = ItemModel(item_id,**data, owner_id=user_id) # Cria o item, desembrulha os dados inseridos e adiciona data e id do user logado
        
        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return item.json(), 201


    # Atualiza os valores de um item já existente no banco
    @jwt_required()
    def put(self, item_id):
        user_id = int(get_jwt_identity()) # Pega o id do user logado
        data = Item.arguments.parse_args()
        
        # Pega o item selecionado pelo usuario no banco
        item_finded = ItemModel.find_item(item_id)

        # Checa se o item existe
        if not item_finded:
            return {"message": "Item not found"}, 404 #Not found

        # Checa se é o dono quem está tentando atualizar o item
        if item_finded.owner_id != user_id:
            return {"message": "You are not allowed to update this item."}, 403 # Acess Denied

        # Atualiza os dados inseridos
        if item_finded:
            item_finded.update_item(**data)
            return item_finded.json(), 200 #sucessful
        item = ItemModel(item_id, **data)

        try:
            item.update_item()
        except:
            return {"message": "An internal error ocurred trying to save item."}, 500 # Internal Server Error
        return item.json(), 201
    

    # Remove do banco o item selecionado
    @jwt_required()
    def delete(self, item_id):
        user_id = int(get_jwt_identity()) # Pega o id do user logado
        item = ItemModel.find_item(item_id)

        # Checa se o item existe
        if not item:
            return {"message": "Item not found"}, 400 #Bad request

        # Checa se é o dono quem está tentando deletar o item
        if item.owner_id != user_id:
            return{"message": "You are not allowed to delete this item."}, 403 # Acess Denied

        try:
            item.delete_item()
            return {'message': 'Item deleted.'}
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error