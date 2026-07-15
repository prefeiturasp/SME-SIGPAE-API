import re


def is_alpha_numeric_and_has_single_space(descricao):
    return bool(re.match(r"[A-Za-z0-9\s]+$", descricao))
