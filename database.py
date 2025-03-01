from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm import scoped_session, sessionmaker

# Create a new SQLAlchemy instance
db = SQLAlchemy()

# Create a scoped session
Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=db.engine))

# Use the scoped session in your application
def get_session():
    return Session()
