# Gestao-de-Inventario-para-pequenos-varejistas
Desenvolvimento de um Sistema Web de Gestão de Inventário e Fidelização de Clientes para o Pequeno Varejo de Tintas

## Preparar e executar o projeto

Este projeto é uma aplicação Django. Não há uma etapa de compilação que gere um executável; para preparar os arquivos estáticos para publicação, use o comando `collectstatic` descrito abaixo.

### Requisitos

- Python 3.10 ou superior
- PowerShell no Windows (ou terminal equivalente)

### Instalação local

Abra o PowerShell na pasta raiz do projeto e crie o ambiente virtual:

```powershell
py -m venv .venv
```

Ative o ambiente e instale as dependências:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Com o ambiente ativo, o prompt do PowerShell começa com `(.venv)`. Se a ativação for bloqueada por uma política de execução de scripts, permita scripts locais para o seu usuário:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirme a alteração quando solicitado e execute novamente `.\.venv\Scripts\Activate.ps1`. Essa configuração vale para o usuário atual do Windows. Como alternativa, use `.\.venv\Scripts\python.exe` para executar o Python do ambiente sem ativá-lo.

### Migrações e execução

Crie/aplique as migrações do banco de dados e inicie o servidor de desenvolvimento:

```powershell
python manage.py migrate
python manage.py runserver
```

A aplicação estará disponível em <http://127.0.0.1:8000/>.

O banco SQLite está configurado em `dados/jb_tintas.db`. Faça uma cópia desse arquivo antes de aplicar migrações se precisar preservar os dados existentes.

Para encerrar o servidor, pressione `Ctrl+C`. Para sair do ambiente virtual, execute:

```powershell
deactivate
```

### Preparar arquivos estáticos

Para reunir os arquivos estáticos do projeto e do Django na pasta `staticfiles`, execute:

```powershell
python manage.py collectstatic --noinput
```

Essa etapa é normalmente usada no processo de publicação. O servidor de desenvolvimento (`runserver`) não substitui a configuração de um servidor de produção.

### Executar os testes automatizados

Com o ambiente virtual ativo, execute os testes de regras de negócio:

```powershell
python manage.py test inventario.tests
```

Os testes usam o executor integrado do Django e um banco de dados temporário; não alteram o banco de dados local em `dados/jb_tintas.db`.

Antes de publicar em produção, configure pelo menos `DEBUG=False`, uma `SECRET_KEY` segura carregada de variável de ambiente e os domínios em `ALLOWED_HOSTS`. Os valores atuais de desenvolvimento em `jb_sistema/settings.py` não devem ser usados como configuração de produção.
