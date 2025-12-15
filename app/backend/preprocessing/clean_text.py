import re


# All types of patterns in Windoes event viewer
class Patterns:
    HEX_PATTERN = re.compile(r"0x[0-9A-Fa-f]+")
    NUMBER_PATTERN = re.compile(r"\b\d+\b")



def clean_message(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = Patterns.HEX_PATTERN.sub("<HEX>", text)
    text = Patterns.NUMBER_PATTERN.sub("<NUM>", text)

    return text.strip()
