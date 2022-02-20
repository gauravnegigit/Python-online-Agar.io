"""
main server script for running the agar.io server 
"""

import socket 
from _thread import * 
import pickle
import random 
import math
import time


s = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET , socket.SO_REUSEADDR , 1)

# setting main constants 

PORT = 5555 
BALL_RADIUS = 5
START_RADIUS = 7 

ROUND_TIME = 60 * 5 
MASS_LOSS_TIME = 7 

WIDTH , HEIGHT = 1000 , 500 

HOST_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST_NAME)

# try to connect to the server 
try :
    s.bind((SERVER_IP , PORT))
except socket.error as e :
    print(str(e))
    print("Server could not start !")
    quit()

s.listen()

# all the dynamic variables are here 
players= {}
balls = []
connections = 0 
id = 0 
colors = [(255,0,0), (255, 128, 0), (255,255,0), (128,255,0),(0,255,0),(0,255,128),(0,255,255),(0, 128, 255), (0,0,255), (0,0,255), (128,0,255),(255,0,255), (255,0,128),(128,128,128), (0,0,0)]
start  = False 
stat_time = 0 
game_time = "Starting soon"
nxt = 1 

# all the functions to be used for teh game 
def release_mass(players):
    """
    releases the mass of players
    """

    for player in players:
        p = players[player]
        if p["score"] > 8 :
            p["score"] = math.floor(p["score"] * 0.95)


def check_collison(players , balls):
   """
   checks if any of the player have collided with any of the balls 
   """

   to_delete = []
   for player in players :
       p = players[player]
       x = p["x"]
       y = p["y"]

       for ball in balls :
           bx = ball[0]
           by = ball[1]

           dis = math.sqrt((x - bx)**2 + (y - by)**2)
           if dis <= START_RADIUS + p["score"] :
               p["score"] += 0.5 
               balls.remove(ball)

def player_collision(players):
    """checks for player collsion and handles that collsion"""

    sort_players = sorted(players , key = lambda x: players[x]["score"])
    for x , player1 in enumerate(sort_players):
        for player2 in sort_players[x + 1 : ] :
            p1x = players[player1]["x"]
            p1y = players[player1]["y"]

            p2x = players[player2]["x"]
            p2y = players[player2]["y"]

            dis = math.sqrt((p1x - p2x)**2 + (p1y - p2y)**2)
            if dis < players[player2]["score"] - players[player1]["score"] * 0.85 :
                players[player2]["score"] = math.sqrt(players[player2]["score"]**2 + players[player1]["score"]**2)
                players[player1]["score"] = 0 
                players[player1]["x"] , players[player1]["y"] = get_start_location(players)
                print(players[player2]["name"] , " ate " , players[player1]["name"])


def create_balls(balls , n):
    """
    creates balls on the screen 
    """

    for i in range(n):
        run = True 
        while run :
            stop = True 
            x = random.randrange(0 , WIDTH)
            y = random.randrange(0 , HEIGHT)

            for player in players :
                p = players[player]
                dis = math.sqrt((x - p["x"])**2 + (y - p["y"])**2)
                if dis <= START_RADIUS + p["score"] :
                    stop = False 
                    break 

            if stop :
                run = False 
        
        balls.append((x , y, random.choice(colors)))


def get_start_location(players):
    """
    picks a staring locatio for a player based on teh other player locations """

    while True :
        stop = True 
        x = random.randrange(0 , WIDTH)
        y = random.randrange(0 , HEIGHT)

        for player in players :
            p = players[player]
            dis = math.sqrt((x - p["x"])**2 + (y - p["y"])**2)

            if dis <= START_RADIUS + p["score"] :
                stop = False 
                break 
        
        if stop :
            break 
    
    return (x , y)


def threaded_client(conn , id):
    """method for running threads to run all the clients along with the server simultaneously !"""

    global connections , players , balls , game_time , nxt , start 

    current_id = id 

    # receive a name from the client 
    data = conn.recv(16)
    name = data.decode("utf-8")
    print(name , "connected to teh server .")

    # setting properties for each new player 
    color = colors[current_id]
    x , y = get_start_location(players)
    players[current_id] = {"x" : x , "y" : y , "color" : color , "score" : 0 , "name" : name}


    #pickle data and send initial info to clients
    conn.send(str.encode(str(current_id)))

    # server will receive basic commands from client and thus it will send back all of teh other clients info 

    while True :
        if start :
            game_time = round(time.time() - start_time)

            if game_time >= ROUND_TIME :
                start = False 
            else :
                if game_time // MASS_LOSS_TIME == nxt :
                    nxt += 1
                    release_mass(players)
                    print(f"{name} Mass depleting")
        
        try :
            # receive data from client 
            data = conn.recv(32)

            if not data :
                break 
            
            data = data.decode("utf-8")

            if data.split(" ")[0] == "move":
                split_data = data.split(" ")
                x = int(split_data[1])
                y = int(split_data[2])
                players[current_id]['x'] = x 
                players[current_id]['y'] = y

                # only check for collison if the game has started 
                if start :
                    check_collison(players , balls)
                    player_collision(players)
                
                # if the amount of balls is less than 150 create more 
                if len(balls) < 150 :
                    create_balls(balls , random.randrange(100 , 150))
                    print("Generating more orbs !")
                
                send_data = pickle.dumps((balls , players , game_time))
            
            elif data.split(" ")[0] == "id":
                send_data = str.encode(str(current_id))

            elif data.split(" ")[0] == "jump":
                send_data = pickle.dumps((balls , players , game_time))

            else :
                send_data = pickle.dumps((balls , players ,game_time))

            conn.send(send_data)
        
        except Exception as e :
            print(e)
            break 
            
        time.sleep(0.001)
    
    # when user disconnects 
    print("NAME : " , name , " Client ID : " , current_id , " disconnected !")
    connections -= 1
    try :
        del players[current_id]
    except :
        pass 

    conn.close()

# MAINLOOP FOR TEH CONNECTIONS 

# creatin balls for teh game
create_balls(balls , random.randrange(200 , 250))
print("Setting up level !")
print("WAITING FOR CONNECTIONS !")

while True :
    host , addr = s.accept()
    print("Connected to : " , addr)

    # starting the game when a client on the server computer connects to teh server 
    if addr[0] == SERVER_IP and not(start):
        start = True 
        start_time = time.time()
        print("GAME STARTED !")
    
    connections += 1 
    start_new_thread(threaded_client, (host , id))
    id += 1 

print("SERVER IS OFFLIEN !")
