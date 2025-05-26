from flask_restful import Resource, reqparse
from models.item_models import ItemModel
from flask_jwt_extended import jwt_required, get_jwt_identity

#TODO: fazer docstring de todas as funções e classes
class Items(Resource):

    def get(self):
        return {'items': [item.json() for item in ItemModel.query.all()]} # SELECT * FROM Item
    

class Item(Resource):
    arguments = reqparse.RequestParser()
    arguments.add_argument('description', type=str, required=True, help="The field 'description' can not be left blank")
    arguments.add_argument('disposal', type=bool, required=True, help="The field 'disposal' can not be left blank")


    def get(self, item_id):
        item = ItemModel.find_item(item_id)
        if item:
            return item.json()
        return {'message': 'Item not found.'}, 404 # not found
    

    @jwt_required()
    def post(self, item_id):
        if ItemModel.find_item(item_id):
            return {"message": "Item id'{}' already exists.".format(item_id)}, 400 # Bad resquest
        
        user_id = get_jwt_identity()
        data = Item.arguments.parse_args()
        item = ItemModel(item_id,**data, owner_id=user_id)
        

        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return item.json(), 201


    @jwt_required()
    def put(self, item_id):
        user_id = get_jwt_identity()
        data = Item.arguments.parse_args()
        
        item_finded = ItemModel.find_item(item_id)

        if item_finded:
            item_finded.update_item(**data)
            return item_finded.json(), 200 #sucessful
        item = ItemModel(item_id, **data)

        if item_finded.owner_id != user_id:
            return{"message": "You are not allowed to update this item."}, 403 # Acess Denied

        try:
            item.update_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 # Internal Server Error
        return item.json(), 201
    

    @jwt_required()
    def delete(self, item_id):

        user_id = get_jwt_identity( )
        
        item = ItemModel.find_item(item_id)

        if item.owner_id != user_id:
            return{"message": "You are not allowed to delete this item."}, 403 # Acess Denied

        if item:
            try:
                item.delete_item()
            except:
                return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error
            return {'message': 'Item deleted.'}
        return {'message': 'Item not found'}, 404 #not founded