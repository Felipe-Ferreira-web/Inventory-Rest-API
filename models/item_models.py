from sql_alchemy import data
from sqlalchemy.orm import relationship
from date import Time


class ItemModel(data.Model):
    
    __tablename__ = 'items'

    item_id = data.Column(data.Integer, primary_key=True)
    description = data.Column(data.String(40))
    disposal = data.Column(data.Boolean, default=True)
    date = data.Column(data.String(20), default=Time.register_time)
    owner_id = data.Column(data.Integer)


    def __init__(self, item_id, description, disposal, owner_id):
        self.item_id = item_id
        self.description = description
        self.disposal = disposal
        self.owner_id = owner_id
    

    def json(self):
        return {
            'item_id': self.item_id,
            'description': self.description,
            'disposal': str(self.disposal),
            'date': self.date,
            'owner_id': self.owner_id
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


    def update_item(self, description, disposal):
        self.description = description
        self.disposal = disposal
        self.save_item()


    def delete_item(self):
        data.session.delete(self)
        data.session.commit()