import multiprocessing

# Define o número de workers com base nos núcleos da CPU
workers = multiprocessing.cpu_count() * 2 + 1

# Endereço e porta que o Gunicorn vai ouvir
bind = "unix:intranet_auvo.sock"

# Permissões do arquivo de socket
umask = 0o007

# Tempo máximo que um worker pode ficar sem responder
timeout = 120

# Logs
accesslog = '-'
errorlog = '-'

# Endereço que o Gunicorn vai usar para comunicar com o Nginx
bind = "unix:intranet_auvo.sock"
# Informa ao Gunicorn para usar o worker do eventlet
worker_class = 'eventlet'
