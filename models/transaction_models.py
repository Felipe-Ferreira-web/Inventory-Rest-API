from sql_alchemy import data
from date import Time

class TransactionModel(data.Model):

    __tablename__ = 'transactions'


    transaction_id = data.Column(data.Integer, primary_key=True)
    date = data.Column(data.String(20), default=Time.register_time)
    disposal = data.Column(data.Boolean, default=False) #Retirar linha
    item_id = data.Column(data.Integer) #Importar valor de outras tabelas posteriormente
    item = data.Column(data.String(40)) #Importar valor de outras tabelas posteriormente
    user_id = data.Column(data.Integer) #Importar valor de outras tabelas posteriormente
    owner_id = data.Column(data.String(40)) #Importar valor de outras tabelas posteriormente

    
    
    def __init__(self, item_id, item, user_id, owner_id):
        self.item_id = item_id
        self.item = item
        self.user_id = user_id
        self.owner_id = owner_id


    def json(self):
        return {
            'transaction_id': self.transaction_id,
            'item_id': self.item_id,
            'item': self.item,
            'user_id': self.user_id,
            'owner_id': self.owner_id,
            'disposal': self.disposal,
            'date': self.date   
        }
    
    
    def update_transaction(self,transaction):
        self.transaction = transaction
    

    def save_transaction(self):
        data.session.add(self)
        data.session.commit()