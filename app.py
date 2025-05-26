from flask import Flask, jsonify
from flask_restful import Api
from resourcers.item_resources import Items, Item
from resourcers.user_resourcers import User, UserRegister, UserLogin, UserLogout
from resourcers.transaction_resourcers import Transactions, LoanTransaction, DevolutionTransaction
from flask_jwt_extended import JWTManager
from blacklist import BLACKLIST


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Secret'
app.config['JWT_BLACK_LIST_ENABLED'] = True
api = Api(app)
jwt = JWTManager(app)


@app.before_request
def create_data():
    data.create_all()


@jwt.token_in_blocklist_loader
def verify_blocklist(jwt_header, jwt_payload):
    return jwt_payload['jti'] in BLACKLIST

@jwt.revoked_token_loader
def invalid_access_token(jwt_header, jwt_payload):
    return jsonify({'message': 'You have been logged out'}) # unauthorized


api.add_resource(Items, '/items')
api.add_resource(Item, '/items/<int:item_id>')
api.add_resource(User, '/users/<int:user_id>')
api.add_resource(UserRegister, '/signup')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogout, '/logout')
api.add_resource(Transactions,'/transactions')
api.add_resource(LoanTransaction,'/loans')
api.add_resource(DevolutionTransaction,'/devolution')

if __name__ == '__main__':
    from sql_alchemy import data
    data.init_app(app)
    app.run(debug=True)

#http://127.0.0.1:5000/items