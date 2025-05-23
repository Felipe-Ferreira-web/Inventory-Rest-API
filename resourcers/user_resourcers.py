from flask_restful import Resource, reqparse
from models.user_models import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from secrets import compare_digest
from blacklist import BLACKLIST

#TODO: usar docstrings em todas as funções e classes
class User(Resource):

    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json()
        return {'message': 'User not found.'}, 404 #not found


    @jwt_required()
    def delete(self, user_id):
        user = UserModel.find_user(user_id)

        if user:
            try:
                user.delete_user()
            except:
                return {'message': 'An internal error ocurred trying to delete user.'}, 500 #Internal Server Error
            return {'message': 'user deleted successfully.'}
        return {'message': 'User not found'}, 404 #not founded
    


class UserRegister(Resource):

    def post(self):

        arguments = reqparse.RequestParser()
        arguments.add_argument('login', type=str, required=True, help="The field 'login' can not be left blank")
        arguments.add_argument('username', type=str, required=True, help="The field 'username' can not be left blank")
        arguments.add_argument('password', type=str, required=True, help="The field 'password' can not be left blank")
        data = arguments.parse_args()

        if UserModel.find_by_login(data['login']):
            return {"message": "The login '{}' already exists.".format(data['login'])}
        
        user = UserModel(**data)
        user.save_user()
        return {'message': 'User created successfully!'}, 201 # Created
    


class UserLogin(Resource):

   @classmethod
   def post(cls):
        
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

    @jwt_required()
    def post(self):
        jwt_id = get_jwt()['jti']
        BLACKLIST.add(jwt_id)
        return{'message': 'Logged out sucessfully!'}, 200
