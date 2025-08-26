![coverage](coverage.svg)
![build](https://img.shields.io/badge/build-passing-green)
![license](https://img.shields.io/badge/license-GPL-green)

![python-version](https://img.shields.io/badge/python-3.13-blue)
![django-version](https://img.shields.io/badge/django-5.2-blue)
![pipenv-version](https://img.shields.io/badge/pipenv-2023.11.15-blue)

# Estratégia de Transformação Digital e Governo Aberto na SME

Como um governo pode atuar para garantir o bem comum de todos? Na SME, acreditamos que um dos meios para isso seja garantir transparência e prestação de contas e constante relação entre governo e sociedade para o desenvolvimento e implementação de políticas públicas. 

A Portaria SME nº 8.008, de 12 de novembro de 2018 oficializou a estratégia da Secretaria Municipal de Educação de SP para que nossas ações sejam pautadas nos princípios de Governo Aberto e para usarmos os valores e benefícios do mundo digital para melhorarmos nossos processos e serviços para os cidadãos. 
Com isso, pretendemos: 
- aumentar os níveis de transparência ativa e de abertura de dados, garantindo a proteção de dados pessoais; 
- instituir metodologias ágeis e colaborativas como parte do processo de desenvolvimento e de evolução de sistemas administrativos e de serviços digitais; 
- fortalecer o controle das políticas educacionais e da aplicação de recursos por parte da gestão e da sociedade; 
- promover espaços e metodologias de colaboração entre governo, academia, sociedade civil e setor privado. 

O [Ateliê do Software](http://forum.govit.prefeitura.sp.gov.br/uploads/default/original/1X/c88a4715eb3f9fc3ceb882c1f6afe9e308805a17.pdf) é uma das ferramentas para operacionalização. Baseado em um modelo de contratação inspirado pelos movimentos ágil e de Software Craftsmanship, trabalhamos com equipes multidisciplinares para o desenvolvimento de produtos que beneficiam toda a comunidade escolar (técnicos da SME e DREs, gestores, professores, alunos e famílias) e concretizam os objetivos da Estratégia de Transformação Digital e Governo Aberto “Pátio Digital”.

# Conteúdo

1. [Sobre o Produto](#sobre-o-produto) 
2. [Sobre o Time](#sobre-o-time) 
3. [Como surgiu](#como-surgiu)  
4. [Links Úteis](#links-úteis)  
5. [Comunicação](#comunicação)  
6. [Como contribuir](#como-contribuir)  
7. [Repositórios](#repositórios)  
8. [Instalação e Configuração](#instalação-e-configuração)
 
# Sobre o Produto

O Sistema de Gestão do Programa de Alimentação Escolar: **SIGPAE** foi desenvolvido pela **Secretaria Municipal de Educação** juntamente com a equipe técnica da **Coordenadoria de Alimentação Escolar** para facilitar e auxiliar o gerenciamento de processos e informações do **Programa de Alimentação Escolar no Município de São Paulo**.

## Objetivos de Negócio

- Promover transparência e agilidade nos processos, acesso de dados e geração de relatórios;
- Desenvolver módulos do sistema adaptáveis e alinhados às necessidades reais dos usuários;
- Fortalecer o controle das políticas educacionais e da aplicação de recursos por parte da gestão e da sociedade;
- Integrar setores, melhorar a eficiência e o fluxo de trabalho;
- Diminuir o fluxo de papéis e planilhas e agilizar o acesso às informações;
- Permitir a integração com sistemas novos ou já existentes;
- Automatizar os processos internos de fornecimento e distribuição da alimentação escolar.

## Personas

**Quem:** Direção Escolar
**Características e necessidades:** responsável pela gestão da escola, com necessidade de otimização de tempo. O sistema é essencial para melhor controle das solicitações realizadas pela UE e demandas de DRE e CODAE

**Quem:** Assistente Técnico de Educação e Nutricionista
**Características e necessidades:** responsável pela gestão das solicitações de alimentação no núcleo de gestão de contratos na CODAE, com necessidade de organização do recebimento das diversas solicitações das UEs

**Quem:** Nutricionista de Dieta Especial
**Características e necessidades:** responsável pela validação de solicitações e prescrição da Dieta Especial, tem necessidade de otimização do processo para revisão, encaminhamento e fornecimento da dieta nas escolas. Processos burocráticos, dolorosos e com decisões de alto impacto para os estudantes

**Quem:** Nutricionista P&D
**Características e necessidades:** responsável pela gestão de produtos (homologação, correção, suspensão e avaliação de reclamação e solicitação de análise sensorial) solicitados pelas empresas terceirizadas, com a necessidade de controle do que pode ser utilizados nas unidades escolares

**Quem:** Diretoria Regional de Educação (DRE)
**Características e necessidades:** responsável pelo gerenciamento das solicitações realizadas pelas escolas que administra, com a necessidade de otimizar e controlar as diversas solicitações das unidades escolares. Para fiscalização e controle das solicitações geradas
  
## Funcionalidades

**Gestão de Alimentação**
- Inclusão de Alimentação
- Solicitação de Kit Lanche
- Suspensão de Alimentação
- Alteração de Cardápio
- Relatórios

**Gestão de Produtos**
- Homologação de produto
- Suspensão e ativação de produto
- Registro de reclamação
- Analise sensorial
- Correção do produto
- Relatórios

**Dieta Especial**
- Solicitação de Dieta
- Cancelamento de Dieta
- Autorização de Dieta
- Criação de Protocolos de Dieta Especial
- Alteração de UE
- Relatórios

## Roadmap

- Release 1 - Gestão de Alimentação
- Release 2 - Gestão de Produtos e Dieta Especial
- Release 3 – CoreSSO
- Release 4 – Gestão de nutricionistas
- Release 5 - Medição Inicial EMEF (visão UE)
- Release 6 - Medição Inicial EMEF (visão DRE e CODAE)
- Release 7 - Medição Inicial CEI e EMEI
- Release 8 - Cardápio
- Release 9 - Supervisão

Detalhamento do roadmap: https://whimsical.com/roadmap-geral-sigpae-C2tThx2G9GpuVviBeHZ5me@VsSo8s35X1aaSatHxnJFRV 

Fluxos: https://whimsical.com/fluxos-i7SkAADB94XRhRMd2afif

# Sobre o Time

| Papel                | Titular                       | Suplente                      |
| -------------------- | ----------------------------- | ----------------------------- |
| Product Owner        | Andrea Wang e Daniela Chichon | Elisete Pereira               |
| Agente de Governança | Juliana Demay                 | Fernando Gonsales             |
| Gerente de Projeto   | Aline Freitas                 |                               |
| Scrum Master         |                               |                               |
| Designer de Serviços | Caio Dib                      |                               |
| Analista de negócios | Jaqueline Sargi               |                               |
| Analista UX/UI       | Joilson Day                   |                               |
| Analista Programador | Calvin Rossignoli             | Rodolpho Lima e João Mesquita |
| Analista de teste    | Paula Pimentel                |                               |

## Protótipos

**Protótipo Navegável:**

**Visão Escola:**
https://www.figma.com/file/52MKvjiFFjoy7WLuvLLjAi/Spt_13-ALIMENTA%C3%87%C3%83O-Terceirizadas_sprint13-230719?node-id=0%3A25539

**Visão CODAE:**
https://www.figma.com/file/52MKvjiFFjoy7WLuvLLjAi/Spt_13-ALIMENTA%C3%87%C3%83O-Terceirizadas_sprint13-230719?node-id=0%3A36995

**Visão DRE:** https://www.figma.com/file/52MKvjiFFjoy7WLuvLLjAi/Spt_13-ALIMENTA%C3%87%C3%83O-Terceirizadas_sprint13-230719?node-id=0%3A43643

**Mapeamento inicial de fluxos:** https://drive.google.com/drive/folders/1mGy5On44p_wHBldWoEKyLrBTG98mhZaC?usp=sharing

# Links Úteis

**Homologação:**

[https://hom-sigpae.sme.prefeitura.sp.gov.br/](https://hom-sigpae.sme.prefeitura.sp.gov.br/)

**Produção:**

[https://sigpae.sme.prefeitura.sp.gov.br/](https://sigpae.sme.prefeitura.sp.gov.br/)

# Comunicação:

| Canal de comunicação                                                         | Objetivos                                                                         |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| [Issues do Github](https://github.com/prefeiturasp/SME-SIGPAE-API/issues) | - Sugestão de novas funcionalidades<br> - Reportar bugs<br> - Discussões técnicas |

# Como contribuir

Contribuições são **super bem vindas**! Se você tem vontade de construir o SIGPAE conosco, veja o nosso [guia de contribuição](./CONTRIBUTING.md) onde explicamos detalhadamente como trabalhamos e de que formas você pode nos ajudar a alcançar nossos objetivos. Lembrando que todos devem seguir  nosso [código de conduta](./CODEOFCONDUCT.md).

# Repositórios

Informar os repositórios de código que envolvem a solução:

[SME-SIGPAE-API] [https://github.com/prefeiturasp/SME-SIGPAE-API](https://github.com/prefeiturasp/SME-SIGPAE-API)

[SME-SIGPAE-FRONTEND]
[https://github.com/prefeiturasp/SME-SIGPAE-Frontend](https://github.com/prefeiturasp/SME-SIGPAE-Frontend)
 
# Instalação e Configuração

## Pré-requisitos

* git
* Docker
* Docker compose

## Banco de dados no Docker

Vamos rodar apenas o banco de dados em Docker, para isto crie uma pasta fora do projeto com o nome `sme-docker`.

```
mkdir sme-docker
cd sme-docker
```

E dentro da pasta crie um arquivo `docker-postgres.yml`

**Importante:** se você já estiver usando a porta 5432 na sua máquina, então mude a porta do host, ex. 5433.

E troque `HOME` para o path absoluto do projeto SME-SIGPAE-API.

```yml
version: '3.1'

services: 
  db:
    image: postgres:14.17-alpine
    restart: always
    env_file:
      - HOME/SME-SIGPAE-API/.env
    volumes:
      - ./pgdata:/var/lib/postgresql/data
    ports:
      - 5433:5432

  pgadmin4:
    image: dpage/pgadmin4
    restart: always
    ports:
      - 9090:9090
    volumes:
      - ./pgbkp:/var/lib/pgadmin/storage/
```

## Build da imagem do banco de dados

### Execução da imagem do banco de dados

Abra um terminal na raiz do projeto e execute o seguinte para o desenvolvimento local:

```
$ docker-compose -f docker-postgres.yml up -d
```

### Rodando o Celery

Na pasta `sme-docker` rodar o comando

```
docker-compose -f docker-celery.yml up -d
```

Na pasta `SME-SIGPAE-API`, com a virtualenv ativa rode

```
celery -A config worker --beat -S sme_sigpae_api.dados_comuns.utils.NaiveDatabaseScheduler --loglevel=info
```


### Rodando o backend

Pré-requisitos:

* Python 3.13.3
* pipenv versão 2023.11.15

Para instalação dos pré-requisitos utilizando o Pyenv, abra um terminal na pasta do backend do projeto na sua máquina e execute os comandos abaixo:

```shell
# Atualize o pyenv
$ pyenv update

# Instale a versão necessária do Python
$ pyenv install 3.13.3

# Defina a versão do Python para a pasta
$ pyenv local 3.13.3

$ pip install pipenv==2023.11.15

# Crie o ambiente virtual e instale as dependências do projeto
$ pipenv install --dev

# Habilite o ambiente virtual
$ pipenv shell

# Mude para a branch development
$ git checkout -b development origin/development

# Execute as migrações
$ python manage.py migrate

# Execute o script para carregar os dados do sistema
$ python manage.py carga_dados
```
