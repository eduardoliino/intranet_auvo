# Intranet Auvo

![Logo](app/static/img/logo_nova.png)

## Sobre o Projeto

A Intranet Auvo é uma aplicação web desenvolvida em Python (Flask) para comunicação interna e gestão de RH. Centraliza avisos, eventos, FAQ, organograma, ouvidoria e um módulo de Newsletter (posts, reações, comentários e enquetes) em um único portal.

Perfis de acesso:
- Colaborador: acesso ao conteúdo e interações.
- Administrador: gerenciamento de colaboradores e conteúdos (avisos, eventos, destaques, links, FAQ, newsletter) e configurações.

---

## Funcionalidades

Para Colaboradores
- Dashboard com aniversariantes, próximos eventos e últimos avisos
- Avisos, Organograma, Lista de Colaboradores, Calendário de Eventos, FAQ
- Ouvidoria (anônima ou identificada)
- Newsletter: visualizar posts, reagir, comentar e participar de enquetes

Para Administradores
- Gestão de colaboradores (adicionar manualmente, importar .xlsx, editar, remover)
- Gestão de avisos, destaques, eventos, links úteis, FAQ
- Newsletter: criar/editar posts, gerenciar enquetes e resultados
- Configurações de cargos, departamentos e organograma

---

## Tecnologias

Backend
- Python 3.8+
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-Session
- Flask-SocketIO (eventlet)
- Pandas, OpenPyXL

Frontend
- HTML5 + Jinja2, CSS, JavaScript
- Bootstrap 5, Alpine.js, Tom Select

Banco de Dados
- MySQL/MariaDB (recomendado) ou SQLite para desenvolvimento

---

## Instalação e Configuração

Pré-requisitos
- Python 3 instalado

Passo a passo
1) Criar e ativar o ambiente virtual
   - Windows: `python -m venv venv && venv\Scripts\activate`
   - macOS/Linux: `python -m venv venv && source venv/bin/activate`

2) Instalar dependências
   - `pip install -r requirements.txt`

3) Configurar variáveis de ambiente
   - Copie `.env.example` para `.env` e ajuste valores:
     - `SECRET_KEY`: chave secreta da aplicação
     - `DATABASE_URL`: URL do banco (ex.: `mysql+pymysql://usuario:senha@localhost/intranet_auvo`)
     - `FLASK_ENV`: `development` ou `production`

4) Migrar o banco de dados
   - `flask db upgrade`

5) Popular dados básicos
   - Permissões e usuário admin: `flask seed`
   - Dados de exemplo da Newsletter (opcional): `flask seed_newsletter`

---

## Execução

Inicie o servidor:
- `python run.py`

Acesse:
- Local: `http://127.0.0.1:5000`
- Rede local: use o IP exibido no terminal (ex.: `http://192.168.x.x:5000`)

Observação: verifique o firewall liberando a porta 5000 quando necessário.

---

## Estrutura do Projeto (completa, exceto migrations e venv)

```
intranet_auvo/
  .env
  .env.example
  .gitignore
  gunicorn.conf.py
  pap.md
  README.md
  requirements.txt
  run.py
  app/
    __init__.py
    auth.py
    colaborador_routes.py
    models.py
    routes.py
    admin_routes/
      __init__.py
      avisos.py
      cargos_departamentos.py
      destaques.py
      eventos.py
      faq.py
      links.py
      ouvidoria.py
      sentimento.py
      utils.py
    newsletter/
      __init__.py
      models.py
      routes.py
      utils.py
    static/
      css/
        newsletter.css
        style.css
      js/
        dashboard.js
        faqPublico.js
        gerenciarAvisos.js
        gerenciarCalendario.js
        gerenciarDestaques.js
        gerenciarEventos.js
        gerenciarFaq.js
        gerenciarOuvidoria.js
        latest_news_card.js
        listarColaboradores.js
        newsletter-api.js
        newsletter-ui.js
        organograma.js
        ouvidoria.js
        reactions-ui.js
      img/
        logo.png
        logo_nova.png
        default_avatar.png
        sentimento/ (ícones)
      fotos_colaboradores/ (imagens de colaboradores)
    templates/
      base.html
      index.html
      login.html
      aviso_detalhe.html
      faq.html
      newsletter.html
      newsletter_enquete_modal.html
      newsletter_post_modal.html
      organograma.html
      ouvidoria.html
      admin/
        _newsletter_posts_list.html
        adicionar_colaborador_manual.html
        adicionar_faq_pergunta.html
        calendario.html
        edit_colaborador.html
        edit_faq_pergunta.html
        gerenciar_avisos.html
        gerenciar_cargos_departamentos.html
        gerenciar_colaboradores.html
        gerenciar_colaboradores_hub.html
        gerenciar_destaques.html
        gerenciar_eventos.html
        gerenciar_faq.html
        gerenciar_faq_categorias.html
        gerenciar_links.html
        gerenciar_newsletter.html
        gerenciar_organograma_config.html
        gerenciar_ouvidoria.html
        importar_colaboradores.html
        listar_colaboradores.html
        sentimento.html
      partials/
        _multi_swap_reactions.html
        _news_post_comments.html
        _news_post_footer.html
        _news_post_reactions.html
        _url_preview.html
        news_enquete_card.html
        news_post_card.html
```

---

## Newsletter (resumo)

Rotas e páginas dedicadas em `/newsletter`. Exemplos de uso da API:

Reagir a um post
```
POST /api/news/post/<post_id>/reacao
{"tipo":"like"}
```

Votar em uma enquete
```
POST /api/news/enquete/<enquete_id>/voto
{"opcoes":[1]}
```

---

## Autor

Eduardo Lino — [eduardoliino](mailto:eduardoliino)

