def strike(text: str) -> str:
    result = ""
    for c in text:
        result = result + c + "\u0336"
    return result
