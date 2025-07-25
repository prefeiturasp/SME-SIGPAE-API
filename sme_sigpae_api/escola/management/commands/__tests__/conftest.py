import pytest
from model_bakery import baker


@pytest.fixture(
    params=[
        # codigo eol, total esperado
        ("000213", 246),
        ("094731", 827),
        ("000086", 491),
    ]
)
def escola_total_params(request):
    return request.param


@pytest.fixture(
    params=[
        # codigo eol, total esperado
        (
            "000094",
            {
                "manha": 225,
                "intermediario": 0,
                "tarde": 223,
                "vespertino": 0,
                "noite": 0,
                "integral": 0,
                "total": 448,
            },
        ),
        (
            "019444",
            {
                "manha": 0,
                "intermediario": 0,
                "tarde": 0,
                "vespertino": 0,
                "noite": 0,
                "integral": 280,
                "total": 280,
            },
        ),
        (
            "307902",
            {
                "manha": 0,
                "intermediario": 0,
                "tarde": 0,
                "vespertino": 0,
                "noite": 0,
                "integral": 102,
                "total": 102,
            },
        ),
        (
            "309117",
            {
                "manha": 0,
                "intermediario": 0,
                "tarde": 0,
                "vespertino": 0,
                "noite": 0,
                "integral": 311,
                "total": 311,
            },
        ),
        (
            "400867",
            {
                "manha": 0,
                "intermediario": 0,
                "tarde": 0,
                "vespertino": 0,
                "noite": 0,
                "integral": 157,
                "total": 157,
            },
        ),
        (
            "200115",
            {
                "manha": 163,
                "intermediario": 161,
                "tarde": 0,
                "vespertino": 186,
                "noite": 175,
                "integral": 0,
                "total": 685,
            },
        ),
    ]
)
def escola_total_por_periodo_params(request):
    return request.param


@pytest.fixture
def escola_sheila_1():
    return baker.make("Escola", codigo_eol="094595")


@pytest.fixture
def escola_sheila_2():
    return baker.make("Escola", codigo_eol="094641")


@pytest.fixture
def escola_sheila_3():
    return baker.make("Escola", codigo_eol="094633")


@pytest.fixture
def escola_sheila_4():
    return baker.make("Escola", codigo_eol="200069")


@pytest.fixture
def escola_lorena_1():
    return baker.make("Escola", codigo_eol="091898")


@pytest.fixture
def escola_lorena_2():
    return baker.make("Escola", codigo_eol="309040")


@pytest.fixture
def escola_lorena_3():
    return baker.make("Escola", codigo_eol="092037")


@pytest.fixture
def aluno_com_codigo_eol():
    return baker.make("Aluno", codigo_eol="1234567")
