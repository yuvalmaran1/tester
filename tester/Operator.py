"""
Operator.py
===========
Operator dataclass and bcrypt-based password utilities.
"""
from dataclasses import dataclass
import bcrypt


@dataclass
class Operator:
    id: int
    username: str
    display_name: str
    role: str          # 'operator' | 'admin'
    active: bool

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "username":     self.username,
            "display_name": self.display_name,
            "role":         self.role,
            "active":       self.active,
        }


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False
