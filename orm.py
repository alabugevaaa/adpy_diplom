from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('postgresql://test:1234@localhost/diplom')
Session = sessionmaker(bind=engine)
session = Session()


class ResultSearch(Base):
    __tablename__ = 'result_search'

    def __str__(self):
        return f'{self.id} {self.link}'

    id = Column(Integer, primary_key=True)
    link = Column(String(250), nullable=False)
    points = Column(Float(), nullable=False)
    top1 = Column(String(250), nullable=False)
    top2 = Column(String(250), nullable=False)
    top3 = Column(String(250), nullable=False)


def create_all():
    Base.metadata.create_all(engine)


create_all()


def add_result(link, points, top1, top2, top3):
    result = ResultSearch(link=link, points=points, top1=top1, top2=top2, top3=top3)

    session.add(result)
    session.commit()


def get_top(count):
    return session.query(ResultSearch).order_by(desc(ResultSearch.points)).limit(count).all()


def delete_all():
    return session.query(ResultSearch).delete()
