# Guia de Implementação da Intranet Auvo na AWS

Este guia detalha o passo a passo para implementar a aplicação da Intranet Auvo num ambiente de produção na AWS, utilizando EC2 para a aplicação e RDS para a base de dados.

## Fase 1: Criação da Infraestrutura na AWS

Antes de colocar o código no servidor, precisamos de criar o ambiente na AWS.

### 1. Criar a Base de Dados (Amazon RDS)

O RDS irá gerir a nossa base de dados MySQL de forma segura e escalável.

1.  Aceda à **Consola da AWS** e procure pelo serviço **RDS**.
2.  Clique em **"Create database"**.
3.  Escolha **"Standard create"** e selecione o motor **"MySQL"**.
4.  Em **"Templates"**, selecione a opção **"Free tier"** para evitar custos iniciais.
5.  Em **"Settings"**, defina:
    * **DB instance identifier:** `intranet-auvo-db`
    * **Master username:** `intranet_user`
    * **Master password:** Crie uma palavra-passe forte e segura. **Anote esta palavra-passe, o utilizador e o nome da base de dados.**
6.  Em **"Connectivity"**:
    * Expanda a secção **"Additional configuration"**.
    * Em **"Initial database name"**, digite `intranet_auvo`.
7.  Ainda em **"Connectivity"**, na secção **"VPC security group"**, selecione **"Create new"**. Dê um nome ao novo Security Group, como `rds-sg`.
8.  Clique em **"Create database"**. A criação pode demorar alguns minutos.
9.  Após a criação, clique na instância da base de dados e copie o **"Endpoint"** no separador "Connectivity & security". **Guarde este endereço.**

### 2. Criar o Servidor da Aplicação (Amazon EC2)

Esta será a máquina virtual onde a sua aplicação irá correr.

1.  Na Consola da AWS, procure pelo serviço **EC2**.
2.  Clique em **"Launch instance"**.
3.  Dê um nome à instância, como `intranet-auvo-server`.
4.  Em **"Application and OS Images"**, selecione **"Ubuntu"**. Mantenha a versão LTS (Long Term Support) selecionada.
5.  Em **"Instance type"**, escolha `t2.micro` (geralmente está no Free Tier).
6.  Em **"Key pair (login)"**, crie um novo par de chaves se ainda não tiver um. Dê um nome (ex: `auvo-key`) e descarregue o ficheiro `.pem`. **Guarde este ficheiro num local seguro, pois é a sua palavra-passe para aceder ao servidor.**
7.  Em **"Network settings"**:
    * Clique em **"Edit"**.
    * Em **"Security group name"**, selecione **"Create new security group"** e nomeie-o como `web-server-sg`.
    * Adicione as seguintes regras de entrada (**Inbound rules**):
        * **SSH (Porta 22):** Source `My IP` (para que apenas você possa aceder ao servidor).
        * **HTTP (Porta 80):** Source `Anywhere`.
        * **HTTPS (Porta 443):** Source `Anywhere`.
8.  Clique em **"Launch instance"**.

### 3. Configurar a Comunicação entre EC2 e RDS

Agora, vamos permitir que o nosso servidor se ligue à base de dados.

1.  Volte para o serviço **RDS**.
2.  Selecione o grupo de segurança que criou para o RDS (`rds-sg`).
3.  Vá ao separador **"Inbound rules"** e clique em **"Edit inbound rules"**.
4.  Clique em **"Add rule"**.
    * **Type:** `MYSQL/Aurora`.
    * **Source:** Selecione o campo de pesquisa e escolha o security group do seu servidor EC2 (`web-server-sg`).
5.  Clique em **"Save rules"**.

## Fase 2: Implementação do Código no Servidor EC2

Agora vamos ligar-nos ao servidor que criámos e configurar a aplicação.

### 1. Ligar ao Servidor

Use o ficheiro `.pem` que descarregou para se ligar via SSH. Encontre o IP público da sua instância EC2 no separador "Instances".

```bash
# No seu computador local, no terminal
# Certifique-se de que o ficheiro .pem tem as permissões corretas
chmod 400 caminho/para/auvo-key.pem

# Ligue-se substituindo o IP
ssh -i "caminho/para/auvo-key.pem" ubuntu@IP_PUBLICO_DO_EC2
```

### 2. Instalar Pacotes e Clonar o Projeto

```bash
# Dentro do servidor EC2

# 1. Atualizar e instalar pacotes do sistema
sudo apt update
sudo apt install python3-pip python3-dev python3-venv nginx git -y

# 2. Clonar o seu projeto do GitHub/GitLab/etc.
git clone [https://github.com/eduardoliino/intranet_auvo.git](https://github.com/eduardoliino/intranet_auvo.git)

# 3. Entrar na pasta do projeto
cd intranet_auvo
```

### 3. Configurar o Ambiente Python

```bash
# 1. Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar as dependências da aplicação
pip install -r requirements.txt
```

### 4. Criar o Ficheiro de Variáveis de Ambiente (`.env`)

Aqui vamos configurar as palavras-passe e endereços para o ambiente de produção.

```bash
# Use o editor nano para criar o ficheiro
nano .env
```

Dentro do editor, cole o seguinte conteúdo, **substituindo os valores em maiúsculas** pelas informações do seu RDS e uma nova chave secreta:

```
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY="GERAR_UMA_NOVA_CHAVE_SECRETA_FORTE_AQUI"
DATABASE_URL="mysql+pymysql://SEU_UTILIZADOR_RDS:SUA_PALAVRA_PASSE_RDS@SEU_ENDPOINT_DO_RDS/intranet_auvo"
```

> **Dica para `SECRET_KEY`:** Pode gerar uma chave segura no terminal do Python com `python3 -c 'import secrets; print(secrets.token_hex(24))'`.

Pressione `Ctrl+X`, depois `Y` e `Enter` para guardar.

### 5. Preparar a Base de Dados

```bash
# Executar as migrações para criar as tabelas no RDS
flask db upgrade

# Criar o utilizador administrador inicial na nova base de dados
flask seed
```

### 6. Configurar o Servidor Web (Gunicorn + Nginx)

#### a. Configurar o Nginx

O Nginx será a porta de entrada para os utilizadores e irá encaminhar o tráfego para a sua aplicação Flask.

```bash
# Criar o ficheiro de configuração do Nginx
sudo nano /etc/nginx/sites-available/intranet_auvo
```

Cole o seguinte conteúdo. **Atenção:** Se o seu nome de utilizador não for `ubuntu`, ajuste os caminhos.

```nginx
server {
    listen 80;
    # Quando tiver um domínio, coloque aqui. Por enquanto, pode usar o IP.
    server_name SEU_IP_PUBLICO_OU_DOMINIO.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/intranet_auvo/intranet_auvo.sock;
    }

    # Servir ficheiros estáticos diretamente pelo Nginx (mais rápido)
    location /static {
        alias /home/ubuntu/intranet_auvo/app/static;
    }
}
```

Agora, ative esta configuração:

```bash
# Cria um link simbólico para ativar o site
sudo ln -s /etc/nginx/sites-available/intranet_auvo /etc/nginx/sites-enabled

# Remove a configuração padrão do Nginx
sudo rm /etc/nginx/sites-enabled/default

# Testa a sintaxe da configuração
sudo nginx -t

# Reinicia o Nginx para aplicar as alterações
sudo systemctl restart nginx
```

#### b. Configurar o Gunicorn para correr como um serviço (Systemd)

Isto garantirá que a sua aplicação inicie automaticamente se o servidor reiniciar e continue a correr em segundo plano.

```bash
# Criar o ficheiro de serviço
sudo nano /etc/systemd/system/intranet_auvo.service
```

Cole o seguinte conteúdo. **Atenção aos caminhos novamente.**

```ini
[Unit]
Description=Gunicorn instance to serve Intranet Auvo
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/intranet_auvo
Environment="PATH=/home/ubuntu/intranet_auvo/venv/bin"
ExecStart=/home/ubuntu/intranet_auvo/venv/bin/gunicorn --config gunicorn.conf.py run:app

[Install]
WantedBy=multi-user.target
```

Agora, inicie e habilite o serviço:

```bash
# Iniciar o serviço pela primeira vez
sudo systemctl start intranet_auvo

# Habilitar o serviço para iniciar junto com o sistema
sudo systemctl enable intranet_auvo

# (Opcional) Verificar o estado do serviço
sudo systemctl status intranet_auvo
```

**Pronto!** Neste ponto, deve conseguir aceder à sua aplicação Intranet Auvo digitando o IP público da sua instância EC2 no navegador.

## Fase 3: Domínio e Segurança (Opcional, mas recomendado)

### 1. Apontar um Domínio (Route 53)

1.  Vá ao serviço **Route 53** na AWS.
2.  Crie uma "Hosted Zone" para o seu domínio (ex: `auvo.com.br`).
3.  Crie um registo do tipo "A" para o seu subdomínio (ex: `intranet.auvo.com.br`) e aponte-o para o **IP público** da sua instância EC2.

### 2. Ativar HTTPS com Certbot (Let's Encrypt)

Depois de o domínio estar a apontar para o IP (pode demorar alguns minutos a propagar), ligue-se novamente ao seu EC2 e execute:

```bash
# Instalar o Certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Executar o Certbot para Nginx
sudo certbot --nginx
```
