import json
from datetime import datetime


def log_create(protocolo_padrao, user=None):
    historico = {}

    historico["created_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    historico["user"] = (
        {
            "uuid": str(user.uuid),
            "email": user.email,
            "username": user.username,
            "nome": user.nome,
        }
        if user
        else user
    )
    historico["action"] = "CREATE"

    editais = []
    for edital in protocolo_padrao.editais.all():
        editais.append(edital.numero)

    substituicoes = []
    for substituicao in protocolo_padrao.substituicoes.all():
        alimentos_substitutos = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.alimentos_substitutos.all()
        ]
        subs = [
            {"uuid": str(sub.uuid), "nome": sub.nome}
            for sub in substituicao.substitutos.all()
        ]

        substitutos = [*alimentos_substitutos, *subs]
        substituicoes.append(
            {
                "tipo": {"from": None, "to": substituicao.tipo},
                "alimento": {
                    "from": None,
                    "to": {
                        "id": substituicao.alimento.id,
                        "nome": substituicao.alimento.nome,
                    },
                },
                "substitutos": {"from": None, "to": substitutos},
            }
        )

    historico["changes"] = [
        {
            "field": "criado_em",
            "from": None,
            "to": protocolo_padrao.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
        },
        {"field": "id", "from": None, "to": protocolo_padrao.id},
        {
            "field": "nome_protocolo",
            "from": None,
            "to": protocolo_padrao.nome_protocolo,
        },
        {
            "field": "orientacoes_gerais",
            "from": None,
            "to": protocolo_padrao.orientacoes_gerais,
        },
        {"field": "status", "from": None, "to": protocolo_padrao.status},
        {"field": "uuid", "from": None, "to": str(protocolo_padrao.uuid)},
        {"field": "substituicoes", "changes": substituicoes},
        {"field": "editais", "from": None, "to": editais},
    ]

    protocolo_padrao.historico = json.dumps([historico])
    protocolo_padrao.save()


def log_update(
    instance,
    validated_data,
    substituicoes_old,
    substituicoes_new,
    new_editais,
    old_editais,
    user=None,
):
    historico = {}
    changes = diff_protocolo_padrao(instance, validated_data, new_editais, old_editais)
    changes_subs = diff_substituicoes(substituicoes_old, substituicoes_new)

    if changes_subs:
        changes.append({"field": "substituicoes", "changes": changes_subs})

    if changes:
        historico["updated_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        historico["user"] = (
            {
                "uuid": str(user.uuid),
                "email": user.email,
                "username": user.username,
                "nome": user.nome,
            }
            if user
            else user
        )
        historico["action"] = "UPDATE"
        historico["changes"] = changes

        hist = json.loads(instance.historico) if instance.historico else []
        hist.append(historico)

        instance.historico = json.dumps(hist)


def diff_protocolo_padrao(instance, validated_data, new_editais, old_editais):
    changes = []

    if instance.nome_protocolo != validated_data["nome_protocolo"]:
        changes.append(
            {
                "field": "nome_protocolo",
                "from": instance.nome_protocolo,
                "to": validated_data["nome_protocolo"],
            }
        )

    if instance.orientacoes_gerais != validated_data["orientacoes_gerais"]:
        changes.append(
            {
                "field": "orientacoes_gerais",
                "from": instance.orientacoes_gerais,
                "to": validated_data["orientacoes_gerais"],
            }
        )

    if instance.status != validated_data["status"]:
        changes.append(
            {"field": "status", "from": instance.status, "to": validated_data["status"]}
        )

    new_editais_list_ordered = set(
        new_editais.order_by("uuid").values_list("uuid", flat=True)
    )
    old_editais_list_ordered = set(
        old_editais.all().order_by("uuid").values_list("uuid", flat=True)
    )
    if new_editais_list_ordered != old_editais_list_ordered:
        changes.append(
            {
                "field": "editais",
                "from": list(old_editais_list_ordered),
                "to": list(new_editais_list_ordered),
            }
        )

    return changes


def diff_substituicoes(substituicoes_old, substituicoes_new):  # noqa C901
    substituicoes = []

    # Tratando adição e edição de substituíções
    if substituicoes_old.all().count() <= len(substituicoes_new):
        for index, subs_new in enumerate(substituicoes_new):
            sub = {}

            try:
                subs = substituicoes_old.all().order_by("id")[index]
            except IndexError:
                subs = None

            if not subs or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {
                        "id": subs.alimento.id if subs else None,
                        "nome": subs.alimento.nome if subs else None,
                    },
                    "to": {
                        "id": subs_new["alimento"].id,
                        "nome": subs_new["alimento"].nome,
                    },
                }

            if not subs or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo if subs else None,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_subs_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_subs_ids, *subs_ids_old]
            ids_news = sorted([s.id for s in subs_new["substitutos"]])

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                from_ = None

                if subs:
                    alimentos_substitutos = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.alimentos_substitutos.all()
                    ]

                    substitutos_ = [
                        {"uuid": str(sub.uuid), "nome": sub.nome}
                        for sub in subs.substitutos.all()
                    ]

                    substitutos = [*alimentos_substitutos, *substitutos_]
                    from_ = (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    )

                sub["substitutos"] = {
                    "from": from_,
                    "to": (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    ),
                }

            if sub:
                substituicoes.append(sub)

    else:
        # trata a remoção de uma substituíção
        for index, subs in enumerate(substituicoes_old.all()):
            sub = {}
            try:
                subs_new = substituicoes_new[index]
            except IndexError:
                subs_new = None

            if not subs_new or subs.alimento.id != subs_new["alimento"].id:
                sub["alimento"] = {
                    "from": {"id": subs.alimento.id, "nome": subs.alimento.nome},
                    "to": {
                        "id": subs_new["alimento"].id if subs_new else None,
                        "nome": subs_new["alimento"].nome if subs_new else None,
                    },
                }

            if not subs_new or subs.tipo != subs_new["tipo"]:
                sub["tipo"] = {
                    "from": subs.tipo,
                    "to": subs_new["tipo"] if subs_new else None,
                }

            al_sub_ids = (
                subs.alimentos_substitutos.all()
                .order_by("id")
                .values_list("id", flat=True)
                if subs
                else []
            )
            subs_ids_old = (
                subs.substitutos.all().order_by("id").values_list("id", flat=True)
                if subs
                else []
            )

            ids_olds = [*al_sub_ids, *subs_ids_old]
            ids_news = (
                sorted([s.id for s in subs_new["substitutos"]]) if subs_new else []
            )

            from itertools import zip_longest

            if any(
                map(
                    lambda t: t[0] != t[1],
                    zip_longest(ids_olds, ids_news, fillvalue=False),
                )
            ):
                to_ = None
                if subs_new:
                    to_ = (
                        [
                            {"uuid": str(s.uuid), "nome": s.nome}
                            for s in subs_new["substitutos"]
                        ]
                        if subs_new["substitutos"]
                        else None
                    )

                alimentos_substitutos = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.alimentos_substitutos.all()
                ]

                substitutos_ = [
                    {"uuid": str(sub.uuid), "nome": sub.nome}
                    for sub in subs.substitutos.all()
                ]

                substitutos = [*alimentos_substitutos, *substitutos_]

                sub["substitutos"] = {
                    "from": (
                        [
                            {"uuid": sub["uuid"], "nome": sub["nome"]}
                            for sub in substitutos
                        ]
                        if substitutos
                        else None
                    ),
                    "to": to_,
                }

            if sub:
                substituicoes.append(sub)

    return substituicoes
