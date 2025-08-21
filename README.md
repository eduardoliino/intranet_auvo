# Intranet Auvo

![Logo](app/static/img/logo_nova.png)

## 📖 Sobre o Projeto

A Intranet Auvo é uma aplicação web desenvolvida em Python com o framework Flask, projetada para ser o portal interno de comunicação e gestão de recursos humanos da empresa Auvo. A plataforma centraliza informações importantes, promove a interação entre os colaboradores e otimiza processos internos.

O sistema conta com dois níveis de acesso:

* **Colaborador:** Acesso às funcionalidades gerais da intranet, como visualização de avisos, calendário de eventos, organograma, FAQ e envio de mensagens para a ouvidoria.
* **Administrador:** Acesso total a todas as funcionalidades, incluindo o gerenciamento de colaboradores, avisos, eventos, destaques, links úteis, FAQ, e a configuração geral do sistema.

---

## ✨ Funcionalidades Principais

### Para Colaboradores

* **Dashboard Inicial:** Visualização rápida de aniversariantes do dia, próximos eventos e os últimos avisos.
* **Avisos:** Acesso a todos os comunicados importantes da empresa.
* **Organograma:** Visualização da estrutura hierárquica da empresa de forma interativa.
* **Lista de Colaboradores:** Encontre informações de contato de outros funcionários.
* **Calendário de Eventos:** Fique por dentro de todos os eventos da empresa.
* **FAQ:** Consulte respostas para as perguntas mais frequentes.
* **Ouvidoria:** Envie sugestões, elogios ou reclamações de forma anônima ou identificada.

### Para Administradores

* **Gerenciamento Completo de Colaboradores:** Adicione (manualmente ou via importação de arquivo .xlsx), edite e remova colaboradores.

* **Gestão de Conteúdo:**

  * Crie e gerencie avisos, destaques da home e eventos do calendário.
  * Administre o FAQ, incluindo categorias e perguntas/respostas.
  * Gerencie os links úteis disponíveis na plataforma.

* **Ouvidoria:** Visualize e gerencie as mensagens recebidas.

* **Configuração do Sistema:**

  * Gerencie cargos e departamentos.
  * Configure a exibição do organograma.

---

## 🚀 Tecnologias Utilizadas

O projeto foi construído com as seguintes tecnologias:

### Backend

* Python 3.8+
* Flask
* Flask-SQLAlchemy
* Flask-Migrate
* Flask-Login
* Pandas
* OpenPyXL

### Frontend

* HTML5 + Jinja2
* CSS3
* JavaScript
* Bootstrap 5
* Alpine.js
* Tom Select

### Banco de Dados

* SQLite

---

## ⚙️ Instalação e Configuração

Siga os passos abaixo para configurar e executar o projeto numa nova máquina.

### Pré-requisitos

* Python 3 instalado.

### Passo a Passo

1. **Copie a Pasta do Projeto**
   Transfira a pasta `intranet_auvo` para a nova máquina.

2. **Abra o Terminal**
   Navegue até à raiz da pasta do projeto (`intranet_auvo`).

3. **Crie e Ative um Ambiente Virtual**

   ```bash
   # Criar o ambiente
   python -m venv venv

   # Ativar no Windows
   venv\Scripts\activate

   # Ativar no macOS/Linux
   source venv/bin/activate
   ```

4. **Instale as Dependências**

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure a Base de Dados**
   Este comando cria o ficheiro `intranet.db` e todas as tabelas necessárias.

   ```bash
   flask db upgrade
   ```

6. **Crie o Utilizador Administrador**
   Abra o shell interativo do Flask para criar o primeiro administrador.

   ```bash
   flask seed
   ```

---

## ▶️ Executar a Aplicação

Com tudo configurado, inicie o servidor Flask.

1. **Execute o Ficheiro `run.py`**
   Este comando irá iniciar o servidor de forma que ele seja acessível na sua rede local.

   ```bash
   python run.py
   ```

2. **Aceda à Aplicação**
   O terminal irá mostrar um endereço de IP local (ex: `http://192.168.1.10:5000`). Use este endereço em qualquer navegador na mesma rede para aceder à intranet. Para aceder no próprio computador, pode usar `http://127.0.0.1:5000`.

**Nota:** Lembre-se de verificar as regras do **firewall** da máquina para garantir que as ligações na porta `5000` são permitidas.

---

## 🗂️ Estrutura do Projeto

```
intranet_auvo/
├── app/
│   ├── static/             # Arquivos estáticos (CSS, JS, Imagens)
│   ├── templates/          # Templates HTML (Jinja2)
│   │   ├── admin/          # Templates da área administrativa
│   │   └── ...
│   ├── __init__.py         # Inicialização do Flask
│   ├── admin_routes/       # Rotas admin
│   │   ├── __init__.py
│   │   ├── utils.py
│   │   ├── cargos_departamentos.py
│   │   ├── avisos.py
│   │   ├── destaques.py
│   │   ├── faq.py
│   │   ├── ouvidoria.py
│   │   ├── eventos.py
│   │   └── links.py
│   ├── auth.py             # Autenticação
│   ├── colaborador_routes.py # Rotas colaborador
│   ├── models.py           # Modelos SQLAlchemy
│   └── routes.py           # Rotas públicas
├── migrations/             # Migrações do banco
├── venv/                   # Ambiente virtual
├── .gitignore              # Ignorados pelo Git
├── app.db                  # Banco SQLite
├── README.md               # Este arquivo
├── requirements.txt        # Dependências
└── run.py                  # Ponto de entrada
```

---

## 👨‍💻 Autor

**Eduardo Lino** - [eduardoliino](mailto:eduardoliino)
