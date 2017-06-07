import sys
from sqlalchemy import ForeignKey, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from flask_login import UserMixin
from itsdangerous import (JSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()

class AuthUser(Base):
	__tablename__ = 'auth_user'
	name = Column(String(80), nullable =False)
	email = Column(String(80), nullable = False, primary_key = True)
	token = Column(String(200), nullable = False)

	def generate_auth_token(self):
		gt = Serializer('SECRET_KEY')
		return gt.dumps({'email': self.email})


class User(UserMixin,Base):
	__tablename__ = 'user'
	name = Column(String(80), nullable = False)
	id = Column(Integer,nullable = False, primary_key = True)
	email = Column(String(80), nullable = False)
	password = Column(String(80), nullable = False)

class Restaurant(Base):
	__tablename__ = 'restaurant'

	name = Column(String(80),nullable = False)
	id = Column(Integer,nullable = False, primary_key = True)
	user = relationship(User)
	owner_id = Column(Integer, ForeignKey('user.id'))
	image = Column(String(80))

	@property
	def serialize(self):
		return {
			'name': self.name,
			'id': self.id,
     		}

class MenuItem(Base):
	__tablename__ = 'menu_item'
	name = Column(String(80), nullable = False)
	id = Column(Integer,nullable = False, primary_key = True)
	course = Column(String(80))
	description = Column(String(1000))
	price = Column(String(10))
	restaurant = relationship(Restaurant)
	restaurant_id = Column(Integer,ForeignKey('restaurant.id'))


# We added this serialize function to be able to send JSON objects in a
# serializable format
	@property
	def serialize(self):
		return {
			'name': self.name,
			'description': self.description,
			'id': self.id,
			'price': self.price,
			'course': self.course,
     		}



engine = create_engine("mysql://root:root@localhost/RESTAURANTMENU")
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)