from secrets import randbelow

from faker import Faker

from sme_sigpae_api.dados_comuns.models import (
    CategoriaPerguntaFrequente,
    PerguntaFrequente,
)

f = Faker("pt-br")
f.seed(420)

for i in range(randbelow(4) + 3):
    cat = CategoriaPerguntaFrequente.objects.create(nome=f.name())
    for j in range(randbelow(6) + 5):
        PerguntaFrequente.objects.create(
            categoria=cat, pergunta=f.text()[:100], resposta=f.text()
        )
