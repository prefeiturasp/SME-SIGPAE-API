#!/usr/bin/env bash
RED='\033[0;31m'
NC='\033[0m' # No Color
echo "Script de carga de dados... Sempre confira os dados para ver se está correto..."

echo "Ao final do script, deseja criar solicitações de teste? (S/N)"
read criar_solicitacoes

echo "Associar admins à escola | dre | codae | terceirizada? VALIDO PARA DESENVOLVIMENTO / HOMOLOGAÇÃO (S/N)"
read associa_admins

echo "Atualizar dados com base na API do EOL em tempo real? (S/N)"
read atualizacao_tempo_real

./manage.py migrate
./manage.py loaddata src/**/fixtures/*.json

./manage.py shell -c "from utility.carga_dados.escola import _2_escola_EMEF_EMEFM_EMEBS_CIEJA"
./manage.py shell -c "from utility.carga_dados.escola import _3_escola_EMEI"
./manage.py shell -c "from utility.carga_dados.escola import _4_escola_CEI"
./manage.py shell -c "from utility.carga_dados.escola import _5_periodo_escolar"
./manage.py shell -c "from utility.carga_dados.escola import _6_periodo_escolar_tipo_alimentacao"

./manage.py shell -c "from utility.carga_dados.escola import _11_atualiza_dre"
./manage.py shell -c "from utility.carga_dados.escola import _12_atualiza_escolas"
./manage.py shell -c "from utility.carga_dados.dieta_especial import _13_dieta_especial"
./manage.py shell -c "from utility.carga_dados.dieta_especial import _16_dieta_especial_carga_alimentos"
# ./manage.py shell -c "from utility.carga_dados.produto import _1_carrega_diagnosticos"

echo -e "${RED}--------CRIANDO GESTORES DAS ESCOLAS----------${NC}"
./manage.py shell -c "from utility.carga_dados.escola import _7_diretor_escola"
echo -e "${RED}--------CRIANDO GESTORES DRE----------${NC}"
./manage.py shell -c "from utility.carga_dados.escola import _8_co_gestores_dre"
echo -e "${RED}--------CRIANDO GESTORES CODAE----------${NC}"
./manage.py shell -c "from utility.carga_dados.escola import _10_codae"

./manage.py shell -c "from utility.carga_dados.escola import _14_faixas_etarias"

echo -e "${RED}Criando cardápios... Devemos criar uma funcionalidade de criação de cardápipos. Esses aqui são TEMPORÁRIOS${NC}"

if [ "$criar_solicitacoes" != "${criar_solicitacoes#[Ss]}" ]; then
  echo "Criando solicitações..."
  ./manage.py shell -c "from utility.carga_dados.cardapio import _2_todas_as_solicitacoes"
  ./manage.py shell -c "from utility.carga_dados.cardapio import _3_solicitacoes_dieta_especial"
fi

if [ "$associa_admins" != "${associa_admins#[Ss]}" ]; then
  echo "Associado admins..."
  ./manage.py shell -c "from utility.carga_dados.escola import _9_associar_admins"
fi

./manage.py shell -c "from utility.carga_dados.cardapio import _1_cardapios"

./manage.py shell -c "from utility.carga_dados import email"

if [ "$atualizacao_tempo_real" != "${atualizacao_tempo_real#[Ss]}" ]; then
  echo -e "${RED}Atualização com dados em tempo real da api do EOL${NC}"
  ./manage.py atualiza_dados_escolas
  ./manage.py atualiza_dres
  ./manage.py atualiza_total_alunos_escolas
fi

echo -e "${RED}Ativando/desativando dinamicamente o vínculo entre TipoUE e Períodos escolares${NC}"
./manage.py shell -c "from src.cardapio.tasks import ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar; ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()"

./manage.py shell -c "from utility.carga_dados.escola import _15_cria_adms"
