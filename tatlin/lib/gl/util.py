def paginate(sequence, n):
    """
    Yield n-sized pieces of sequence.
    """
    for i in range(0, len(sequence), n):
        yield sequence[i : i + n]


def html_color(color):
    if color.startswith("#"):
        color = color[1:]
    parsed = [int(c, 16) / 255 for c in paginate(color, 2)]
    return parsed
