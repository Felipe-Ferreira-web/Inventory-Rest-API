from flask_restful import Resource, reqparse
from models.user_models import UserModel
from models.transaction_models import TransactionModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from secrets import compare_digest
from blacklist import BLACKLIST


class User(Resource):
    """ Recurso para operações relacionadas a usuários.

        Métodos:
            get(user_id): Recupera informações de um usuário pelo seu ID.
            delete(user_id): Exclui o usuário autenticado, removendo também suas transações. """


    def get(self, user_id):
        """ Obtém os dados de um usuário pelo 'user_id'.

            Parâmetros:
                user_id (int): Identificador do usuário a ser buscado.

            Retorno:
                tuple:
                    - Se o usuário for encontrado, retorna os dados em formato JSON.
                    - Se não encontrado, retorna mensagem de erro e código HTTP 404. """
        
        user = UserModel.find_user(user_id)

        if user:
            return user.json()
        return {'message': 'User not found.'}, 404 #not found


    @jwt_required()
    def delete(self, user_id):
        """ Exclui o usuário autenticado.

            Verifica se o usuário existe e se o usuário autenticado tem permissão para deletar (só pode deletar a si mesmo).
            Remove todas as transações associadas ao usuário antes de deletar o usuário.

            Parâmetros:
                user_id (int): Identificador do usuário a ser deletado.

            Retorno:
                tuple:
                    - Se o usuário não existir, retorna mensagem de erro e código HTTP 404.
                    - Se o usuário tentar deletar outro usuário, retorna mensagem de erro e código HTTP 403.
                    - Se houver erro interno na exclusão, retorna mensagem de erro e código HTTP 500.
                    - Se a exclusão for bem-sucedida, retorna mensagem de sucesso. """
        
        user = UserModel.find_user(user_id)
        user_accessed = int(get_jwt_identity())
        
        if not user:
            return {'message': 'User not found'}, 404 #not found
        
        if user.user_id != user_accessed:
            return {"message": "You can not delete other users"}, 403 # Forbidden
        
        try:
            TransactionModel.delete_user_transaction(user_id)
            user.delete_user()
        except:
            return {'message': 'An internal error ocurred trying to delete user.'}, 500 #Internal Server Error
        return {'message': 'user deleted successfully.'}
    
    

class UserRegister(Resource):
    """ Recurso para registro de novos usuários. """


    def post(self):
        """ Registra um novo usuário no sistema.

            - Recebe os dados obrigatórios: 'login', 'username' e 'password'.
            - Verifica se o login já existe.
            - Cria e salva o novo usuário no banco de dados.

            Retorno:
                tuple:
                    - Se o login já existir, retorna mensagem de erro e código HTTP 400.
                    - Se ocorrer erro interno ao salvar, retorna mensagem de erro e código HTTP 500.
                    - Se o usuário for criado com sucesso, retorna mensagem de confirmação e código HTTP 201. """
        
        arguments = reqparse.RequestParser()
        arguments.add_argument('login', type=str, required=True, help="The field 'login' can not be left blank")
        arguments.add_argument('username', type=str, required=True, help="The field 'username' can not be left blank")
        arguments.add_argument('password', type=str, required=True, help="The field 'password' can not be left blank")
        data = arguments.parse_args()

        if UserModel.find_by_login(data['login']):
            return {"message": "The login '{}' already exists.".format(data['login'])}, 400
        
        user = UserModel(**data)

        try:
            user.save_user()
        except: 
            return {'message': 'An internal error ocurred trying to create user.'}, 500 #Internal Server Error
        return {'message': 'User created successfully!'}, 201 # Created

    

class UserLogin(Resource): 
    """ Recurso para autenticação de usuários e geração de token JWT. """


    @classmethod
    def post(cls):  
        """ Autentica um usuário e gera um token de acesso JWT.

            - Recebe 'login' e 'password' via argumentos da requisição.
            - Verifica se o usuário existe e se a senha confere.
            - Em caso de sucesso, gera e retorna um token de acesso JWT.
            - Em caso de falha, retorna mensagem de erro e código HTTP 401.

            Retorno:
                tuple:
                    - Sucesso: dicionário com 'token_accessed' e código HTTP 200.
                    - Falha: mensagem de erro e código HTTP 401. """
        
        arguments = reqparse.RequestParser()
        arguments.add_argument('login', type=str, required=True, help="The field 'login' can not be left blank")
        arguments.add_argument('password', type=str, required=True, help="The field 'password' can not be left blank")
        data = arguments.parse_args()
        
        user = UserModel.find_by_login(data['login'])

        if user and compare_digest(user.password, data['password']):
           access_token = create_access_token(identity=str(user.user_id))
           return {'token_accessed': access_token}, 200 #Ok
        return {'message': 'The username or password is incorrect.'}, 401 # Unauthorized



class UserLogout(Resource):
    """ Recurso para realizar logout do usuário invalidando o token JWT. """


    @jwt_required()
    def post(self):
        """ Realiza o logout do usuário.

            - Obtém o identificador do token JWT atual (jti).
            - Adiciona o jti à blacklist para invalidação do token.
            - Retorna mensagem de sucesso.

            Retorno:
                dict: Mensagem de confirmação do logout e código HTTP 200. """
        
        jwt_id = get_jwt()['jti']
        BLACKLIST.add(jwt_id)
        return{'message': 'Logged out sucessfully!'}, 200
