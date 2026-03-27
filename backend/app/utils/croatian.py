import re


def validate_oib(oib: str) -> bool:
    """Validate Croatian personal identification number (OIB) using ISO 7064 Mod 11,10."""
    oib = oib.strip()
    if not re.match(r"^\d{11}$", oib):
        return False

    s = 10
    for i in range(10):
        d = int(oib[i])
        s = (s + d) % 10
        if s == 0:
            s = 10
        s = (s * 2) % 11

    check = (11 - s) % 11
    return check == int(oib[10])


def validate_mbo(mbo: str) -> bool:
    """Validate Croatian health insurance number (MBO) — exactly 9 digits."""
    return bool(re.match(r"^\d{9}$", mbo.strip()))
