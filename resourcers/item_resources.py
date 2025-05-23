from flask_restful import Resource, reqparse
from models.item_models import ItemModel
from flask_jwt_extended import jwt_required

#TODO: fazer docstring de todas as funções e classes
class Items(Resource):

    def get(self):
        return {'items': [item.json() for item in ItemModel.query.all()]} # SELECT * FROM Item
    


class Item(Resource):
    arguments = reqparse.RequestParser()
    arguments.add_argument('item', type=str, required=True, help="The field 'item' can not be left blank")
    arguments.add_argument('disposal', type=bool, required=True, help="The field 'disposal' can not be left blank")



    def get(self, item_id):
        item = ItemModel.find_item(item_id)
        if item:
            return item.json()
        return {'message': 'Item not found.'}, 404 #not found
    
    
    @jwt_required()
    def post(self, item_id):
        if ItemModel.find_item(item_id):
            return {"message": "Item id'{}' already exists.".format(item_id)}, 400 #Bad resquest
        
        data = Item.arguments.parse_args()
        item = ItemModel(item_id, **data)
        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error
        return item.json(), 201


    @jwt_required()
    def put(self, item_id):
        data = Item.arguments.parse_args()
        item_finded = ItemModel.find_item(item_id)
        if item_finded:
            item_finded.update_item(**data)
            return item_finded.json(), 200 #sucessful
        item = ItemModel(item_id, **data)
        try:
            item.save_item()
        except:
            return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error
        return item.json(), 201
    

    @jwt_required()
    def delete(self, item_id):
        item = ItemModel.find_item(item_id)
        if item:
            try:
                item.delete_item()
            except:
                return {'message': 'An internal error ocurred trying to save item.'}, 500 #Internal Server Error
            return {'message': 'Item deleted.'}
        return {'message': 'Item not found'}, 404 #not founded