from __future__ import annotations

_ENCODE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--",
    "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...", ":": "---...",
    ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    '"': ".-..-.", "$": "...-..-", "@": ".--.-.", " ": "/",
}
_DECODE: dict[str, str] = {v: k for k, v in _ENCODE.items() if k != " "}
_DECODE["/"] = " "


def translate(payload: dict) -> dict:
    text = str(payload.get("text", ""))
    direction = str(payload.get("direction", "encode")).lower()
    if direction == "encode":
        encoded = " ".join(_ENCODE.get(ch.upper(), "") for ch in text)
        return {"result": encoded.strip()}
    if direction == "decode":
        words = text.split(" / ")
        decoded = " ".join(
            "".join(_DECODE.get(code, "") for code in word.split())
            for word in words
        )
        return {"result": decoded}
    return {"error": f"direction must be 'encode' or 'decode', got {direction!r}"}
