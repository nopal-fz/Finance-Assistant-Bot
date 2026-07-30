def format_idr(amount: int) -> str:
    """Format integer to IDR currency string."""
    return f"Rp {amount:,}".replace(",", ".")
