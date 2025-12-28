import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/lenskart")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)