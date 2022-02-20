import socket 
import pickle 

class Network :
    def __init__(self) -> None:
        self.cleint = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.host = "Your IPv4 address"
        self.port = 5555
        self.addr = (self.host , self.port)
    
    def connect(self , name):
        """
        this method helps to connect to server and returns teh id of teh client """

        self.cleint.connect(self.addr)
        self.cleint.send(str.encode(name))
        val = self.cleint.recv(8)
        return int(val.decode())
    
    def disconnect(self):
        """
        disconnects from the server
        """
        self.cleint.close()

    def send(self , data , pick = False):
        try :
            if pick :
                self.cleint.send(pickle.dumps(data))
            else :
                self.cleint.send(str.encode(data))

            reply = self.cleint.recv(2048 * 4)

            try :
                reply = pickle.loads(reply)
            except Exception as e :
                print(e)

            return reply 
        except socket.error as e :
            print(e)
