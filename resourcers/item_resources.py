from flask_restful import Resource, reqparse
from models.item_models import ItemModel
from flask_jwt_extended import jwt_required, get_jwt_identity


# (Items) classe designada a todos os items
class Items(Resource):

    # Pega todas os items postados
    def get(self):
        return {'items': [item.json() for item in ItemModel.query.all()]} # SELECT * FROM Item
    

# (Item) classe designada a manipulação de items
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
        
        user_id = int(get_jwt_identity())
        data = Item.arguments.parse_args()
        item = ItemModel(item_id,**data, owner_id=user_id)
        
        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return item.json(), 201

    # Atualiza os valores de um item já existente no banco
    @jwt_required()
    def put(self, item_id):
        user_id = int(get_jwt_identity())
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
        user_id = int(get_jwt_identity())
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