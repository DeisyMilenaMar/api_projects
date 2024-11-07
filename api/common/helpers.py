from uuid import uuid4
from datetime import datetime
from django.utils.crypto import get_random_string

def generate_token(prefix: str = 'token', version: str = '', with_date: bool = False) -> str:
    """
    Generate unique token with configurable prefix, version and date.
    """
    unique_id = uuid4().hex[:12]
    random_str = get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    date_str = datetime.now().strftime('%Y%m%d') if with_date else ''
    return f"{prefix}_{version}{date_str}{unique_id}{random_str}"