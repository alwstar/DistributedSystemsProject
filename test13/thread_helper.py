import threading

def new_thread(target, args=()):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True
    thread.start()
