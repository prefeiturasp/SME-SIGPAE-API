# SME SIGPAE API

## Carga de dados

Em desenvolvimento basta fazer

```
python manage.py carga_dados
```


### Carga de dados em produção

* entre no painel de Admin
* vá até a tabela 'Usuários'
* selecione pelo menos um usuário
* em *Ação*, escolha 'Carga dados'



### Carga de dados de Diretores e Cogestores

Para fazer uma carga de dados dos Diretores e Cogestores em produção:

* entre no painel de Admin
* vá até a tabela de 'PlanilhaDiretorCogestor'
* e faça o upload de uma planilha Excel.


## Painel consolidado (app paineis_consolidados)

Para fazer alguma alteração no painel consolidado é preciso criar um novo arquivo sql seguindo a ordem 
já existente.

Exemplo: `0015_solicitacoes.sql`

Depois é preciso criar uma migração apontando para o sql novo.

Exemplo: criar na pasta migrations o arquivo `0015_solicitacoes.py`.

código:
```
import environ
from django.db import migrations

ROOT_DIR = environ.Path(__file__) - 2

sql_path = ROOT_DIR.path('sql', '0015_solicitacoes.sql')
with open(sql_path, 'r') as f:
    sql = f.read()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('paineis_consolidados', '0014_solicitacoes'),
    ]

    operations = [
        migrations.RunSQL(sql),
    ]
```
então é só aplicar a migração `python manage.py migrate`


## Diagramas

Na diretório diagramas de classes é possível visualizar todos os diagramas das apps django do projeto afim de ajudar no entendimentos das relações entre os modelos.
