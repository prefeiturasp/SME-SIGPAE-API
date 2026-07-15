def ofuscar_email(email):
    m = email.split("@")
    return f'{m[0][0]}{"*" * (len(m[0]) - 2)}{m[0][-1]}@{m[1]}'
