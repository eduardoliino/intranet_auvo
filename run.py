from app import create_app

# create_app() agora retorna 'app' e 'socketio'
app, socketio = create_app()

if __name__ == '__main__':
    # Usa o servidor do SocketIO com o worker eventlet para suportar WebSockets
    socketio.run(app, host='0.0.0.0', debug=True)
