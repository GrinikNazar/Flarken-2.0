def send_long_message(text, max_len=3800):
    lines = text.split("\n")
    message = ""

    for line in lines:
        if len(message) + len(line) + 1 > max_len:
            yield message
            message = line
        else:
            if message:
                message += "\n" + line
            else:
                message = line

    if message:
        yield message
