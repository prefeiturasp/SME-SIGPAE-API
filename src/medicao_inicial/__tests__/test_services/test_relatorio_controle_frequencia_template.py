from django.template.loader import render_to_string


def test_relatorio_controle_frequencia_agrupa_cabecalho_da_faixa_em_tbody_proprio():
    html = render_to_string(
        "relatorio_controle_frequencia.html",
        {
            "filtros": {},
            "data_relatorio": "26/05/2026",
            "total_matriculados": 0,
            "periodos": [
                {
                    "periodo": "integral",
                    "quantidade": 0,
                    "faixas": [
                        {
                            "nome_faixa": "01 ano a 03 anos e 11 meses",
                            "alunos_por_faixa": [],
                            "dias": [],
                        }
                    ],
                    "alunos_com_dietas_autorizadas": [],
                }
            ],
            "mes_ano_formatado": "MAIO/2026",
            "dias_do_mes": [],
            "matriculados_data_str": "em 26/05/2026",
            "escola_nome": "CEU CEI MENINOS",
            "mes_ano": "05_2026",
        },
    )

    assert 'tbody class="grupo-faixa-cabecalho"' in html
    assert 'tbody class="grupo-faixa-conteudo"' in html
    assert "<td />" not in html
