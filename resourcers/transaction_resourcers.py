from flask_restful import Resource, reqparse
from models.transaction_models import TransactionModel



class Transactions(Resource):
    
    def get(self):
        return {'transactions': [transactions.json() for transactions in TransactionModel.query.all()]}
    
    

class LoanTransaction(Resource):

    
    def get(self,loan_id):
        loan = TransactionModel.find_loan(loan_id)
        if loan:
            return loan.json()
        return {"message": "User's loan not found."}, 404 #not found
    


    #post será usado quando um usuario quiser fazer um empréstimo ele preencherá a tabela com os valores necessarios para tal serem arquivados na tabela
    def post(self):
        
        arguments = reqparse.RequestParser()                                                                                    
        arguments.add_argument('item_id', type=int, required=True, help="The field 'item_id' can not be left blank")
        arguments.add_argument('item', type=str, required=True, help="The field 'item' can not be left blank")
        arguments.add_argument('user_id', type=int, required=True, help="The field 'user_id' can not be left blank")
        arguments.add_argument('owner_id', type=int, required=True, help="The field 'owner_id' can not be left blank")
        data = arguments.parse_args()

        dispo = TransactionModel.query.filter_by(disposal=True).first()
        if dispo:
            return {"message": "'{}' is not available.".format(data['item_id'])}
         
        transaction = TransactionModel(**data)
        transaction.save_transaction()
        return {'message': 'Item transfered successfully!'}, 201 # Created

    

class DevolutionTransaction(Resource):
    ...