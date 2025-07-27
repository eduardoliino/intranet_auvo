# Intranet Auvo

![Logo](app/static/img/logo_nova.png)

## 📖 Descrição

A Intranet Auvo é um portal web interno desenvolvido com a framework Flask em Python. O objetivo do projeto é centralizar a comunicação interna, fornecer ferramentas úteis para os colaboradores e otimizar processos do departamento de RH, criando um ambiente digital coeso e informativo para todos na empresa.

---

## ✨ Funcionalidades

A plataforma está dividida em duas áreas principais: a visão do colaborador e o painel de administração.

### Para Colaboradores
- **Dashboard Principal:** Uma página inicial com acesso rápido a:
  - Comunicados importantes do RH.
  - Aniversariantes do mês.
  - Colaboradores destaque do mês.
  - Próximos eventos da empresa.
- **Canal de Ouvidoria:** Um formulário seguro para enviar sugestões, críticas ou denúncias, com a opção de se identificar ou permanecer anónimo.
- **FAQ (Perguntas Frequentes):** Uma base de conhecimento com busca e filtros para tirar dúvidas comuns sobre a empresa.
- **Sistema de Login:** Autenticação segura para acesso à plataforma.

### Para Administradores (RH)
- **Gestão de Colaboradores:**
  - Adicionar novos colaboradores manualmente através de um formulário.
  - Adicionar múltiplos colaboradores de uma vez via importação de planilha Excel (.xlsx).
  - Listar, editar e remover colaboradores existentes.
- **Gestão de Comunicados:** Interface para criar, visualizar e apagar os avisos que aparecem na dashboard.
- **Gestão de Destaques:** Ferramenta para eleger e exibir os colaboradores destaque de cada mês.
- **Gestão de FAQ:**
  - CRUD completo para criar, editar e apagar perguntas e respostas.
  - Gestão de categorias para organizar o conteúdo do FAQ.
- **Gestão de Ouvidoria:** Painel para visualizar as manifestações recebidas e alterar o seu status (Nova, Em análise, Resolvida).
- **Gestão de Eventos:** Um CRUD interativo para adicionar, editar e remover eventos internos que são exibidos na dashboard.

---

## 🚀 Tecnologias Utilizadas

O projeto foi construído com as seguintes tecnologias:

- **Backend:**
  - **Python 3**
  - **Flask:** Framework principal da aplicação.
  - **Flask-SQLAlchemy:** ORM para interação com a base de dados.
  - **Flask-Migrate:** Controlo de versões do esquema da base de dados.
  - **Flask-Login:** Gestão de autenticação e sessões de utilizadores.
  - **Pandas / OpenPyXL:** Para a funcionalidade de importação de dados a partir de planilhas.

- **Frontend:**
  - **HTML5** (com templates Jinja2)
  - **CSS3**
  - **JavaScript**
  - **Bootstrap 5:** Framework CSS para a estrutura e responsividade.
  - **Alpine.js:** Biblioteca JavaScript para adicionar interatividade à interface.
  - **Tom Select:** Para a criação de listas suspensas (selects) modernas e com busca.

- **Base de Dados:**
  - **SQLite:** Base de dados leve e baseada em ficheiro, ideal para desenvolvimento e pequenas aplicações.

---

## ⚙️ Instalação e Configuração

Siga os passos abaixo para configurar e executar o projeto numa nova máquina.

### Pré-requisitos
- Python 3 instalado.

### Passo a Passo

1.  **Copie a Pasta do Projeto**
    Transfira a pasta `intranet_auvo` para a nova máquina.

2.  **Abra o Terminal**
    Navegue até à raiz da pasta do projeto (`intranet_auvo`).

3.  **Crie e Ative um Ambiente Virtual**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

4.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure a Base de Dados**
    Este comando cria o ficheiro `intranet.db` e todas as tabelas necessárias.
    ```bash
    flask db upgrade
    ```

6.  **Crie o Utilizador Administrador**
    Abra o shell interativo do Flask para criar o primeiro administrador.
    ```bash
    flask shell
    ```
    Dentro do shell, execute os seguintes comandos Python:
    ```python
    from app.models import User
    from app import db
    admin = User(username='admin')
    admin.set_password('sua_senha_segura_aqui')
    db.session.add(admin)
    db.session.commit()
    exit()
    ```

---

## ▶️ Executar a Aplicação

Com tudo configurado, inicie o servidor Flask.

1.  **Execute o Ficheiro `run.py`**
    Este comando irá iniciar o servidor de forma que ele seja acessível na sua rede local.
    ```bash
    python run.py
    ```

2.  **Aceda à Aplicação**
    O terminal irá mostrar um endereço de IP local (ex: `http://192.168.1.10:5000`). Use este endereço em qualquer navegador na mesma rede para aceder à intranet. Para aceder no próprio computador, pode usar `http://127.0.0.1:5000`.

**Nota:** Lembre-se de verificar as regras do **firewall** da máquina para garantir que as ligações na porta `5000` são permitidas.