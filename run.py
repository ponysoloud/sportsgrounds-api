from app import app, sockets

if __name__ == '__main__':
    sockets.run(app, debug=True)
