import socket
import time
import select
from threading import Thread
from socketserver import ThreadingMixIn

class myThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print ("[+] Nouveau thread démarré pour " + ip + ":" + str(port))

    def run(self):
        while True:
            try:
                ready_to_read, ready_to_write, in_error = \
                        select.select([con,], [], [], 5)
            except select.error:
                print("ERROR!!!!!!!!!!!")
                con.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
                con.close()
                # connection error event here, maybe reconnect
                print('connection error')
                break

            if len(ready_to_read) > 0:
                recv = con.recv(2048)
                # do stuff with received data
                print(f'received: {recv}')

            con.send(b"/api/private")


        # while True :
        #     # data = con.recv(2048)
        #     # print("Le serveur a reçu des données:", data)
        #     # # msg = raw_input("Entrez la réponse du serveur ou exit pour sortir:")
        #     # # if msg == 'exit':
        #     # #     break
        #     msg = b"/api/interface/coucou"
        #     con.send(msg)

        #     data = con.recv(2048)
        #     print(data)

        #     time.sleep(2)

# Programme du serveur TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 9999))
mythreads = []

while True:
    s.listen(5)
    print("Serveur: en attente de connexions des clients TCP ...")
    (con, (ip,port)) = s.accept()
    mythread = myThread(ip,port)
    mythread.start()
    mythreads.append(mythread)
for t in mythreads:
    t.join()
