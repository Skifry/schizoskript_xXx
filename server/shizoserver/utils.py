from prompt_toolkit import print_formatted_text, HTML


FACE = (
    r"   __",
    r" / * /",
    "/°/ °\\",
    r"\{—} / ",
)


def tip_say(text: str):
    text = [
        list(line)
        for line in (
            " " * 8
            + "<b><white>Ю. Дицкий</white></b>\n"
            + "\n".join(f'{" " * 8}<b>{i}</b>' for i in text.split("\n"))
        ).split("\n")
    ]
    for y, line in enumerate(FACE):
        for x, symbol in enumerate(line):
            if FACE[y][x] == "*":
                text[y - len(text)][x] = "<orange>*</orange>"
            elif FACE[y][x] == "—":
                text[y - len(text)][x] = "<red>—</red>"
            else:
                text[y - len(text)][x] = f"<b><gray>{FACE[y][x]}</gray></b>"
    return HTML("\n".join("".join(i) for i in text))
