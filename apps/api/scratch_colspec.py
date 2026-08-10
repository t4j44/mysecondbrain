from sqlalchemy import Column, String, cast, create_engine
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import JSON, TEXT, TypeDecorator


class SafeArray(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def __init__(self, item_type):
        super().__init__()
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return value


Base = declarative_base()


class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(String, primary_key=True)
    tags = Column(SafeArray(String))


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert array
obj = TestModel(id="1", tags=["hello", "world"])
session.add(obj)
session.commit()

# Test queries
query1 = session.query(TestModel).filter(cast(TestModel.tags, String).like("%hello%")).all()
print("Cast Like Query count:", len(query1))

query2 = session.query(TestModel).filter(TestModel.tags.like("%hello%")).all()
print("Direct Like Query count:", len(query2))
