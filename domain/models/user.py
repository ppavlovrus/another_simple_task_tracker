from typing import Optional
from datetime import datetime

class User:
    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        password: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __str__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, created_at={self.created_at}, updated_at={self.updated_at})"