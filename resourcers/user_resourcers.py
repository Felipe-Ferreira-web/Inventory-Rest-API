from flask_restful import Resource, reqparse
from models.user_models import UserModel
from models.transaction_models import TransactionModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from secrets import compare_digest
from blacklist import BLACKLIST


# classe para manipulação de users já criados
class User(Resource):

    # Pega as informações do id do user inserido
    def get(self, user_id):
        user = UserModel.find_user(user_id)

        if user:
            return user.json()
        return {'message': 'User not found.'}, 404 #not found

    # Delete o user do id inserido
    @jwt_required()
    def delete(self, user_id):
        user = UserModel.find_user(user_id)
        user_accessed = int(get_jwt_identity()) # Pega o id do user logado
        
        # Checa se o user existe
        if not user:
            return {'message': 'User not found'}, 404 #not found
        
        # Checa se quem está deletendo o usuario é o próprio usuario logado
        if user.user_id != user_accessed:
            return {"message": "You can not delete other users"}, 403 # Forbidden
        
        try:
            TransactionModel.delete_user_transaction(user_id) # Substitui por null na tabela transactions o id do user deletado
            user.delete_user()
        except:
            return {'message': 'An internal error ocurred trying to delete user.'}, 500 #Internal Server Error
        return {'message': 'user deleted successfully.'}
    

# classe para criação de users
class UserRegister(Resource):

    # Cria uma conta com os valores inseridos pelo user
    def post(self):
        arguments = reqparse.RequestParser()
        arguments.add_argument('login', type=str, required=True, help="The field 'login' can not be left blank")
        arguments.add_argument('username', type=str, required=True, help="The field 'username' can not be left blank")
        arguments.add_argument('password', type=str, required=True, help="The field 'password' can not be left blank")
        data = arguments.parse_args()

        # Checa se o campo login já foi usado
        if UserModel.find_by_login(data['login']):
            return {"message": "The login '{}' already exists.".format(data['login'])}, 400
        
        # Cria user
        user = UserModel(**data)

        try:
            user.save_user()
        except: 
            return {'message': 'An internal error ocurred trying to create user.'}, 500 #Internal Server Error
        return {'message': 'User created successfully!'}, 201 # Created

    

# classe para fazer o login do user já criado
class UserLogin(Resource):

   @classmethod
   def post(cls):   
        arguments = reqparse.RequestParser()
        arguments.add_argument('login', type=str, required=True, help="The field 'login' can not be left blank")
        arguments.add_argument('password', type=str, required=True, help="The field 'password' can not be left blank")
        data = arguments.parse_args()
        
        # Pega o login do user já criado no banco
        user = UserModel.find_by_login(data['login'])

        # Checa se a senha e o login inseridos pelo user estão corretos para acessar a conta
        if user and compare_digest(user.password, data['password']):
           access_token = create_access_token(identity=str(user.user_id)) # Cria o token de acesso pelo id do user
           return {'token_accessed': access_token}, 200 #Ok
        return {'message': 'The username or password is incorrect.'}, 401 # Unauthorized


# classe para sair da conta do user
class UserLogout(Resource):

    @jwt_required()
    def post(self):
        jwt_id = get_jwt()['jti']
        BLACKLIST.add(jwt_id)
        return{'message': 'Logged out sucessfully!'}, 200
