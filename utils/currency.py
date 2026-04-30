CURRENCY_MAP = {
    "EUR": "EUR",
    "EURO": "EUR",
    "€": "EUR",

    "USD": "USD",
    "DOLLAR": "USD",
    "AMERICAN DOLLAR": "USD",
    "$": "USD",

    "UAH": "UAH",
    "HRYVNIA": "UAH",
    "UKRAINIAN HRYVNIA": "UAH",
    "₴": "UAH",

    "GBP": "GBP",
    "BRITISH POUND": "GBP",
    "POUND": "GBP",
    "£": "GBP",
}

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "UAH": "₴",
    "GBP": "£",
}


def parse_currency_from_text(text: str) -> str | None:
    """
    Extract explicit currency from input text.
    
    Supports:
    - Prefix symbols: $10, €20, ₴30, £40
    - Suffix codes: 10eur, 20usd, 30uah, 40gbp
    - Standalone codes at start: EUR 10, USD 20
    
    Args:
        text: Input text (e.g., "$50 food pizza" or "10 eur lunch")
    
    Returns:
        Currency code (EUR, USD, UAH, GBP) or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    parts = text.split()
    
    if not parts:
        return None
    
    # Check first part for prefix symbol or standalone code
    first = parts[0].strip()
    
    # Prefix symbol: $, €, ₴, £
    if first and first[0] in CURRENCY_SYMBOLS.values():
        symbol = first[0]
        for code, sym in CURRENCY_SYMBOLS.items():
            if sym == symbol:
                return code
    
    # Amount with suffix code: "10eur", "20usd"
    if first and any(c.isdigit() for c in first):
        # Extract non-digit part after the number
        i = 0
        while i < len(first) and (first[i].isdigit() or first[i] in ".,"):
            i += 1
        if i < len(first):
            suffix = first[i:].upper()
            # Check if suffix matches a currency code/variant
            normalized = CURRENCY_MAP.get(suffix)
            if normalized:
                return normalized
    
    # Standalone code at start: "EUR 10", "USD 20"
    code_check = first.upper()
    if code_check in CURRENCY_MAP:
        return CURRENCY_MAP[code_check]
    
    # Check second part for standalone code (after amount): "10 EUR", "20 USD"
    if len(parts) > 1:
        second = parts[1].upper()
        if second in CURRENCY_MAP:
            return CURRENCY_MAP[second]
    
    return None
