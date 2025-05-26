from flask_restful import Resource, reqparse
from models.transaction_models import TransactionModel
from models.item_models import ItemModel
from  flask_jwt_extended import jwt_required, get_jwt_identity


class Transactions(Resource):
    
    def get(self):
        return {'transactions': [transaction.json() for transaction in TransactionModel.query.all()]}
    
    
class LoanTransaction(Resource):

    def get(self,loan_id):
        loan = TransactionModel.find_loan(loan_id)
        if loan:
            return loan.json()
        return {"message": "User's loan not found."}, 404 #not found
    

    @jwt_required()
    def post(self):
        
        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        data = arguments.parse_args()


        item_id = data['item_id'] # valor que o usuario inseriu
        user_id = get_jwt_identity() # id do usuario logado

        # Pega o item no banco ItemModel
        item = ItemModel.query.get(item_id)

        # Se o item existe
        if not item:                                        
            return {"message": "item not found."}, 404
        
        # Se o item já não está no inventario de quem fez a requisição
        if item.owner_id == user_id:                       
            return {"message": "This item is already in your inventory"}, 400
        

        # Se o item está disponivel
        if item.disposal != True:
            return{"message": "Item is not available for transfer."}, 400
        
        # Altera o status de disposal para indisponivel(False)
        item.disposal = False

        # Faz a transação
        transaction = TransactionModel(
            item_id = item_id,
            from_user_id = item.owner_id,
            to_user_id = user_id,
            disposal = item.disposal)

       
        transaction.save_transaction()
        item.save_item()
        return transaction.json(), 201
    
    
class DevolutionTransaction(Resource):
    ...