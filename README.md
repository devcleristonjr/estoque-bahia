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

Inclui também a tabela de controle do fechamento diário para evitar execução duplicada.

Se você quiser voltar para PostgreSQL no futuro, basta trocar `DATABASE_URL` para o formato `postgresql+psycopg://usuario:senha@host:5432/banco`.

Se precisar criar um novo administrador inicial:

```bash
flask --app run.py create-admin
```

Para executar manualmente o fechamento diário de estoque (mesma rotina usada em produção):

```bash
flask --app run.py zerar-estoques
```

Para testar com uma data específica (idempotência por data local da Bahia):

```bash
flask --app run.py zerar-estoques --data-referencia 2026-09-18
```

## Execução

```bash
flask --app run.py run
```

## Timezone oficial

Todas as operações de data/hora usam timezone de Salvador/Bahia (`America/Bahia`, com fallback para `America/Sao_Paulo`).

## Agendamento diário de zeramento (23:00 Bahia)

O projeto não mantém scheduler interno no Flask (sem loop/sleep). O recomendado é agendar o comando CLI no sistema operacional do servidor.

Exemplo Linux (cron):

```bash
0 23 * * * cd /caminho/estoque-bahia && TZ=America/Bahia flask --app run.py zerar-estoques >> /var/log/estoque-bahia-reset.log 2>&1
```

Exemplo Windows (Task Scheduler):

```powershell
schtasks /Create /TN "EstoqueBahia-ZeramentoDiario" /SC DAILY /ST 23:00 /TR "cmd /c cd /d C:\caminho\estoque-bahia && flask --app run.py zerar-estoques >> logs\zeramento.log 2>&1"
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
