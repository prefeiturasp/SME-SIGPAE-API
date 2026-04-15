# SME-SIGPAE-POC-Testes

## **Teste Automatizado**

- Este projeto visa automatizar API e Front de forma a facilitar a validação de itens de forma regressiva.
- Ele contém os casos de teste do SIGPAE.

<div align="center">
  <img src="./cypress/fixtures/images/image_sigpae.jpg" alt="Descrição da imagem" width="300">
</div>

## **Tecnologias Usadas**

![JavaScript](https://img.shields.io/badge/-Javascript-yellow) ![Cypress](https://img.shields.io/badge/-Cypress-white) ![ESLint](https://img.shields.io/badge/-ESLint-%234B32C3)

## **Pré-requisitos**

- Ter o Node instalado na maquina
- Link de instalação do Node (https://nodejs.org/en)
- Clone o projeto em seu diretório de preferência e execute `npm install` na raiz do projeto

## **Estrutura**

- Cypress
  - Fixtures (pasta com arquivo cypress padrão)
  - e2e (pasta com diretórios de teste API e Front)
  - Screenshots(Pasta onde são armazenadas as capturas de tela da execução dos testes)
  - Support(Pasta com arquivos de comandos para os testes de API e Front do SIGPAE)
  - Videos(Pasta onde ficam armazenados os vídeos da execução dos testes)
  - node_modules(Baixado automaticamente na instalação após o comando npm install)

## **Como executar os testes**

- Abra o serviço de terminal
- Acesse o diretório e após executar o comando `npm install` execute os testes com o comando abaixo:
  - Use o comando `npx cypress run` para execução completa via terminal
  - Use o comando `npx cypress open` para abrir a janela de execução e selecionar os casos a serem executados

  # Fluxo de GitFlow + Instalação Manual do Cypress

## 📌 Fluxo GitFlow Definido

### Branches principais:

- **main**: Automações da esteira de CI/CD (somente merges de aprovados)
- **develop**: branch de integração e desenvolvimento contínuo

### Branches de apoio:

- **feature/**: novas funcionalidades a partir de `develop`
- ***Exemplo de feature/**: feature/127000-nova-funcionalidade (Nro do card antes da descrição)
- **bugfix/**: correções de bugs identificados em `develop`

### Exemplo de fluxo:

```bash
# Nova funcionalidade
 git checkout develop
 git pull origin develop
 git checkout -b feature/nova-funcionalidade
 ...
 git commit -m "feat: nova funcionalidade"
 git push origin feature/nova-funcionalidade
```

```bash
# Corrigir bug em develop
 git checkout develop
 git pull origin develop
 git checkout -b bugfix/corrige-tela-login
 ...
 git commit -m "fix: tela de login não carregava"
 git push origin bugfix/corrige-tela-login
```

---

## ✅ Solução manual para instalar o Cypress (sem erro de certificado)

### 📥 1. Baixe o instalador manualmente

Buscar a versão desejada para instalação. No exemplo abaixo, está sendo utilizada a versão 13.7.0
👉 [Download Cypress 13.17.0 (Windows 64-bit)](https://download.cypress.io/desktop/13.17.0?platform=win32\&arch=x64)

### 📁 2. Crie o caminho esperado no cache

Crie a seguinte pasta na sua máquina:

```
C:\Users\<SEU_USUÁRIO>\AppData\Local\Cypress\Cache\13.17.0
```

Ou execute no terminal:

```cmd
mkdir %LOCALAPPDATA%\Cypress\Cache\13.17.0
```

### 📦 3. Extraia o arquivo baixado na pasta

O download será um `.zip` contendo o Cypress.

Extraia **todo o conteúdo** do `.zip` dentro da pasta:

```
C:\Users\<SEU_USUÁRIO>\AppData\Local\Cypress\Cache\13.17.0
```

⚠️ Importante: Após a extração, **dentro da pasta** `13.17.0` **deve conter a pasta** `Cypress`.

### 🔁 4. Reinstale o Cypress sem tentar baixar novamente

Volte ao terminal e execute:

```bash
npm install cypress@13.17.0 --save-dev
```

O `npm` vai identificar que a versão já está em cache e **não tentará baixar novamente da internet**, evitando o erro de certificado.

### 🧪 5. Teste a instalação

```bash
npx cypress open
```

Se tudo estiver certo, a **interface do Cypress** vai abrir normalmente.
