```bash
# Criar arquivo .env a partir do env-exemplo
cp env-exemplo .env

# Ajustar as variáveis do arquivo .env

# Para subir o container
docker compose -f docker-compose-local.yml up -d

# Para baixar o container
docker compose -f docker-compose-local.yml down

# Para acessar o shell do container
docker exec -it sigpae-api bash
```
