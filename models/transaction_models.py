from sql_alchemy import data
from sqlalchemy.orm import relationship
from date import Time


class TransactionModel(data.Model):

    __tablename__ = 'transactions'

    transaction_id = data.Column(data.Integer, primary_key=True)
    item_id = data.Column(data.Integer, nullable=True) # Puxa o id do item da tabela items
    from_user_id = data.Column(data.Integer, data.ForeignKey('users.user_id'), nullable=True) # Puxa o id de um usuario da tabela user
    to_user_id = data.Column(data.Integer, data.ForeignKey('users.user_id'), nullable=True) # # Puxa o id de um usuario da tabela user
    is_available = data.Column(data.Boolean, default=True)
    date = data.Column(data.String(20), default=lambda: Time.register_time())


    from_user = relationship('UserModel', foreign_keys=[from_user_id], backref='from_transactions') # Cria a relação da tabela users com o from_user_id
    to_user = relationship('UserModel', foreign_keys=[to_user_id], backref='to_transactions') # Cria a relação da tabela users com o to_user_id

    
    def __init__(self, item_id, from_user_id, to_user_id, is_available):
       self.item_id = item_id
       self.from_user_id = from_user_id
       self.to_user_id = to_user_id
       self.is_available = is_available
       
      
    def json(self):
        return {
            'transaction_id': self.transaction_id,
            'item_id': self.item_id,
            'from_user': self.from_user_id,
            'to_user': self.to_user_id,
            'is_available': self.is_available,
            'date':self.date
        }
    
    
    def save_transaction(self):
        data.session.add(self)
        data.session.commit()
    

    def update_transaction(self,transaction):
        self.transaction = transaction
        self.save_transaction()



    # Deleta os valores de user na tabela transactions
    @classmethod
    def delete_user_transaction(cls, user_id):
        data.session.query(cls).filter_by(from_user_id=user_id).update({"from_user_id": None})
        data.session.query(cls).filter_by(to_user_id=user_id).update({"to_user_id": None})
        data.session.commit()