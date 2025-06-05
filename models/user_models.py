from sql_alchemy import data
from sqlalchemy.orm import relationship


class UserModel(data.Model):

    __tablename__ = 'users'

    user_id = data.Column(data.Integer, primary_key=True)
    username = data.Column(data.String(20))
    login = data.Column(data.String(40))
    password = data.Column(data.String(40))

    sent_transactions = relationship("TransactionModel", foreign_keys='TransactionModel.from_user_id') # Cria relação com a tabela transactions
    received_transactions = relationship("TransactionModel", foreign_keys='TransactionModel.to_user_id') # Cria relação com a tabela transactions

    def __init__(self, username, login, password):
        self.username = username
        self.login = login
        self.password = password


    def json(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'login': self.login
        }
    

    # Acha o usuario pelo user_id
    @classmethod
    def find_user(cls, user_id):
        user = cls.query.filter_by(user_id=user_id).first() 
        if user:
            return user
        return None
    
    # Acha o usuario pelo login
    @classmethod
    def find_by_login(cls, login):
        user = cls.query.filter_by(login=login).first() 
        if user:
            return user
        return None
    

    def save_user(self):
        data.session.add(self)
        data.session.commit()


    def update_user(self,user):
        self.user = user


    def delete_user(self):
        data.session.delete(self)
        data.session.commit()