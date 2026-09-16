# language: pt
Funcionalidade: Validar dados de alunos EOL

  Esquema do Cenario: Consultar dados de aluno pelo codigo EOL
    Quando consulto os dados do aluno pelo codigo EOL "<codigo>"
    Entao a consulta do aluno EOL retorna status <status>
    E a resposta do aluno EOL corresponde ao codigo "<codigo>"

    Exemplos:
      | codigo    | status |
      | 8310251   | 200    |
      | 999999999 | 400    |
