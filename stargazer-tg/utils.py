escape_list = ['\\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']


def escape_md_v2(string: str):
    for character in escape_list:
        string = string.replace(character, f"\\{character}")

    return string
