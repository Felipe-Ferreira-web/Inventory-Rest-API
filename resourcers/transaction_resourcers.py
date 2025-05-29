from flask_restful import Resource, reqparse
from models.transaction_models import TransactionModel
from models.item_models import ItemModel
from  flask_jwt_extended import jwt_required, get_jwt_identity


class Transactions(Resource):
    def get(self):
        return {'transactions': [transaction.json() for transaction in TransactionModel.query.all()]}, 200
    
    
class LoanTransaction(Resource):

    # Pega todas as transações feitas
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
