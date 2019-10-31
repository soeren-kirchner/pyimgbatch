def to_int_or_none(value, multiplier=1):
    try:
        value = int(value) * multiplier
        return value
    except:
        return None
