from sql_alchemy import data
from date import Time


class ItemModel(data.Model):

    __tablename__ = 'items'

    item_id = data.Column(data.Integer, primary_key=True)
    item = data.Column(data.String(40))
    disposal = data.Column(data.Boolean)
    date = data.Column(data.String(20), default=Time.register_time)
    #owner_id
    #loan = data.relationship('LoanModel', backref='item', lazy=False)

    

    def __init__(self, item_id, item, disposal):
        self.item_id = item_id
        self.item = item
        self.disposal = disposal
    


    def json(self):
        return {
            'item_id': self.item_id,
            'item': self.item,
            'disposal': self.disposal,
            'date': self.date
        }
    


    @classmethod
    def find_item(cls, item_id):
        item = cls.query.filter_by(item_id=item_id).first() #SELECT * FROM items WHERE item_id = $item_id
        if item:
            return item
        return None
    


    def save_item(self):
        data.session.add(self)
        data.session.commit()



    def update_item(self, item, disposal):
        self.item = item
        self.disposal = disposal



    def delete_item(self):
        data.session.delete(self)
        data.session.commit()