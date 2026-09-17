# Estoque Bahia

Aplicação Flask para controle georreferenciado de pontos de estoque e materiais distribuídos pelos municípios da Bahia.

## Stack

- Python 3.12+
- Flask
- PostgreSQL
- SQLAlchemy
- Flask-Migrate
- Flask-Login
- Bootstrap 5
- Leaflet.js + OpenStreetMap

## Estrutura inicial

- autenticação com Flask-Login
- modelos para territórios, municípios, materiais, pontos de estoque, estoque e movimentações
- upload de imagens em pasta organizada por ano e mês
- dashboard, mapa e CRUD básico de materiais e pontos
- script de importação da planilha de municípios

## Configuração

1. Crie um arquivo `.env` com base em `.env.example`.
2. Para desenvolvimento local, o projeto já vem configurado para SQLite via `DATABASE_URL=sqlite+pysqlite:///estoque_bahia.db`.
3. Ajuste `SECRET_KEY`.

Exemplo:

```env
SECRET_KEY=uma_chave_forte
DATABASE_URL=sqlite+pysqlite:///estoque_bahia.db
APP_ENV=development
```

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Migrações

```bash
flask --app run.py db upgrade
```

Se você quiser voltar para PostgreSQL no futuro, basta trocar `DATABASE_URL` para o formato `postgresql+psycopg://usuario:senha@host:5432/banco`.

Se precisar criar um novo administrador inicial:

```bash
flask --app run.py create-admin
```

## Execução

```bash
flask --app run.py run
```

## Importação geográfica

Se a planilha `Municipios Bahia.xlsx` estiver disponível, execute:

```bash
python scripts/import_municipios.py --file "Municipios Bahia.xlsx"
```

Se o arquivo não existir, o script apenas informa e encerra sem quebrar a aplicação.

## O que já está pronto

- login e logout
- dashboard base
- mapa focado na Bahia
- cadastro de materiais
- cadastro de pontos de estoque
- movimentação inicial de estoque
- upload de foto com validação básica
- estrutura de API JSON preparada

## Próximos passos naturais

1. Refinar o fluxo de edição de estoque e o histórico.
2. Adicionar CRUD administrativo para usuários, territórios e municípios.
3. Implementar seeds opcionais de demonstração e exportações.
