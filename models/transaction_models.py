from sql_alchemy import data
from sqlalchemy.orm import relationship
from date import Time


class TransactionModel(data.Model):

    __tablename__ = 'transactions'

    transaction_id = data.Column(data.Integer, primary_key=True)
    date = data.Column(data.String(20), default=Time.register_time) 


    item_id = data.Column(data.Integer, data.ForeignKey('items.item_id'), nullable=False)
    from_user_id = data.Column(data.Integer, data.ForeignKey('users.user_id'), nullable=False)
    to_user_id = data.Column(data.Integer, data.ForeignKey('users.user_id'), nullable=False)
    disposal = data.Column(data.Boolean, default=True)


    from_user = relationship('UserModel', foreign_keys=[from_user_id], backref='sent_transactions')
    to_user = relationship('UserModel', foreign_keys=[to_user_id], backref='received_transactions')

    
    def __init__(self, item_id, from_user_id, to_user_id, disposal):
       self.item_id = item_id
       self.from_user_id = from_user_id
       self.to_user_id = to_user_id
       self.disposal = disposal
       
      
    def json(self):
        return {
            'transaction_id': self.transaction_id,
            'item_id': self.item_id,
            'from_user': self.from_user_id,
            'to_user': self.to_user_id,
            'disposal': str(self.disposal),
            'date': self.date   
        }
    
    
    def save_transaction(self):
        data.session.add(self)
        data.session.commit()
    

    def update_transaction(self,transaction):
        self.transaction = transaction
        self.save_transaction()