from uuid import uuid4
from datetime import datetime
from django.utils.crypto import get_random_string

def generate_token(prefix: str = 'token', version: str = '', with_date: bool = False) -> str:
    """
    Generate unique token with configurable prefix, version and date.
    Format: prefix_[version][date]hexrandom
    
    Args:
        prefix: Token prefix (default: 'token')
        version: Version string (e.g., 'v1', 'v2')
        with_date: Include current date (default: False)
    
    Returns:
        str: Generated token
        
    Examples:
        generate_token('api', 'v1')      -> 'api_v19b1deb4d3b7dPQW5KLMNP'
        generate_token('trx', with_date=True) -> 'trx_20241030P9b1deb4d3b7dPQW5KLMNP'
    """
    unique = uuid4().hex[:12]
    random = get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    date = datetime.now().strftime('%Y%m%d') if with_date else ''
    
    return f"{prefix}_{version}{date}{unique}{random}"