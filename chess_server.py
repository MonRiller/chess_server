import socket, os, chess, random, shutil, time
import chess.engine
from _thread import *

#Set up socket to accept connections
ServerSocket = socket.socket()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
host = s.getsockname()[0]
port = 1233
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Join with "telnet {} 1233"'.format(host))
print('Waiting for a Connection..')
ServerSocket.listen(100)

#Set up directory to handle games and file for names
try:
    os.remove('names.txt')
except:
    pass
try:
    shutil.rmtree('chess_games')
except:
    pass
if (not "chess_games" in os.listdir()):
    os.mkdir("chess_games/")
if (not "names" in os.listdir()):
    f = open("names.txt", 'w')
    f.close()

def client_thread(connection, addy):
    connection.send(str.encode('\n\nWelcome to Ron\'s mid chess server!\n'))
    name = ''
    first = True
    try:
        while(name == '' or name in [i[:-1] for i in open("names.txt", 'r').readlines()]):
            if(not first):
                connection.send(str.encode("\nThat name is already taken, enter a new name.\n"))
            else:
                connection.send(str.encode('\nWhat is your name?\n'))
            first = False
            response = connection.recv(2048)
            if not response:
                print('Closed connection to: ' + addy)
                connection.close()
                return
            name = response.decode('utf-8')[:-2]
    except:
        pass
    f = open("names.txt", 'a')
    f.write(name + '\n')
    f.close()
    while True:
        try:
            response = ''
            while(not response in ['s', 'm', 'single', 'multi', 'singleplayer', 'multiplayer']):
                connection.send(str.encode('\n{}, do you want to play a singleplayer or multiplayer game? (s/m) '.format(name)))
                response = connection.recv(2048).decode('utf-8')[:-2]
            if(response in ['s', 'single', 'singleplayer']):
                response = ''
                while(not response in [str(i) for i in range(1, 11)]):
                    connection.send(str.encode('\nWhat level do you want to play? (1-10) '))
                    response = connection.recv(2048).decode('utf-8')[:-2]
                engine = chess.engine.SimpleEngine.popen_uci("./stockfish_15_win_x64_avx2/stockfish_15_x64_avx2.exe")
                level = int(response)
                limit = chess.engine.Limit(time = 0.1 * (0.3 ** (10 - level)))
                b = chess.Board()
                machine_first = bool(random.getrandbits(1))
                move = True
                if(machine_first):
                    connection.send(str.encode('\nYou are black\n\n'))
                else:
                    connection.send(str.encode('\nYou are white\n\n'))
                connection.send(str.encode(str(b) + '\n\n'))
                while(not b.is_game_over()):
                    if(machine_first == move):
                        mv = engine.play(b, limit).move
                        if(random.randint(level, 15) < 10):
                            mv = random.choice([i for i in b.legal_moves])
                        b.push(mv)
                        brd = str(b)
                        if(machine_first):
                            brd = brd[::-1]
                        connection.send(str.encode('\n\n{}\n\nEngine played {}\n'.format(brd, mv)))
                    else:
                        while(True):
                            connection.send(str.encode('\nWhat is your move? (UCI format: a2a4) '))
                            response = connection.recv(2048).decode('utf-8')[:-2]
                            try:
                                mv = chess.Move.from_uci(response)
                                if(mv in b.legal_moves):
                                    b.push(mv)
                                    brd = str(b)
                                    if(machine_first):
                                        brd = brd[::-1]
                                    connection.send(str.encode('\n\n{}\nYou played {}\n'.format(brd, mv)))
                                    break
                            except:
                                pass
                            connection.send(str.encode('\nError, try again\n'))
                    move = not move
            else:
                maker = False
                if(len(os.listdir("chess_games")) == 0):
                    connection.send(str.encode('\nThere are no open games, opening a game with your name'))
                    f = open('chess_games/{}'.format(name), 'w')
                    f.close()
                    maker = True
                else:
                    connection.send(str.encode('\nOpen games are:\n'))
                    for i in os.listdir("chess_games"):
                        if(os.path.getsize("./chess_games/{}".format(i)) == 0):
                            connection.send(str.encode('{}\n'.format(i)))
                    response = ''
                    while(not response in ['j', 'm', 'join', 'make']):
                        connection.send(str.encode('\nDo you want to join a game? or make your own? (j/m) '))
                        response = connection.recv(2048).decode('utf-8')[:-2]
                    if(response in ['m', 'make']):
                        f = open('chess_games/{}'.format(name), 'w')
                        f.close()
                        maker = True
                    else:
                        response = ''
                        while (response not in os.listdir("chess_games")):
                            connection.send(str.encode('\nOpen games are:\n'))
                            for i in os.listdir("chess_games"):
                                if(os.path.getsize("./chess_games/{}".format(i)) == 0):
                                    connection.send(str.encode('{}\n'.format(i)))
                            if(response != ''):
                                connection.send(str.encode("\nError with that game name"))
                            connection.send(str.encode("\nWhose game do you want to join?\n"))
                            response = connection.recv(2048).decode('utf-8')[:-2]
                        f = open('chess_games/{}'.format(response), 'w')
                        f.write(name)
                        f.close()
                        connection.send(str.encode("\nJoined {} game.\n".format(response)))
                if(maker):
                    gameName = "./chess_games/{}".format(name)
                    while(os.path.getsize(gameName) == 0):
                        time.sleep(1)
                    f = open(gameName, 'r')
                    opponent = f.read()
                    f.close()
                    connection.send(str.encode("\n{} joined game.\n".format(opponent)))
                    opponent_first = bool(random.getrandbits(1))
                    f = open(gameName, 'w')
                    f.write(str(opponent_first))
                    f.close()
                    time.sleep(3)
                    b = chess.Board()
                    if(not opponent_first):
                        connection.send(str.encode("\nYou are white!\n"))
                        connection.send(str.encode(str(b) + '\n\n'))
                    else:
                        connection.send(str.encode("\nYou are black!\nOpponent to move.\n\n"))
                    turn = True
                    while(not b.is_game_over()):
                        if(turn != opponent_first):
                            mv = ''
                            while(True):
                                connection.send(str.encode('\nWhat is your move? (UCI format: a2a4) '))
                                response = connection.recv(2048).decode('utf-8')[:-2]
                                try:
                                    mv = chess.Move.from_uci(response)
                                    if(mv in b.legal_moves):
                                        b.push(mv)
                                        brd = str(b)
                                        if(opponent_first):
                                            brd = brd[::-1]
                                        connection.send(str.encode('\n\n{}\nYou played {}\n'.format(brd, mv)))
                                        break
                                except:
                                    pass
                                connection.send(str.encode('\nError, try again\n'))
                            f = open(gameName, 'w')
                            f.write(str(mv) + '\n' + b.fen())
                            f.close()
                            time.sleep(2)
                        else:
                            while(True):
                                time.sleep(1)
                                if(opponent not in [i[:-1] for i in open('names.txt', 'r').readlines()]):
                                    os.remove(gameName)
                                    connection.send(str.encode('\n{} has left the game.\n'.format(opponent)))
                                    break
                                if(not os.path.getsize(gameName) == 0):
                                    f = open(gameName,'r')
                                    lines = f.readlines()
                                    mv = lines[0][:-1]
                                    b.set_fen(lines[1])
                                    f.close()
                                    f = open(gameName, 'w')
                                    f.close()
                                    brd = str(b)
                                    if(opponent_first):
                                        brd = brd[::-1]
                                    connection.send(str.encode('\n\n{}\n\n{} played {}\n'.format(brd, opponent, mv)))
                                    break
                            if(opponent not in [i[:-1] for i in open('names.txt', 'r').readlines()]):
                                break
                        turn = not turn
                    os.remove(gameName)
                else:
                    opponent = response
                    gameName = "./chess_games/{}".format(opponent)
                    time.sleep(3)
                    opponent_first = (open(gameName, 'r').read() == "False")
                    f = open(gameName, 'w')
                    f.close()
                    b = chess.Board()
                    if(not opponent_first):
                        connection.send(str.encode("\nYou are white!\n"))
                        connection.send(str.encode(str(b) + '\n\n'))
                    else:
                        connection.send(str.encode("\nYou are black!\nOpponent to move.\n\n"))
                    turn = True
                    while(not b.is_game_over()):
                        if(turn != opponent_first):
                            mv = ''
                            while(True):
                                connection.send(str.encode('\nWhat is your move? (UCI format: a2a4) '))
                                response = connection.recv(2048).decode('utf-8')[:-2]
                                try:
                                    mv = chess.Move.from_uci(response)
                                    if(mv in b.legal_moves):
                                        b.push(mv)
                                        brd = str(b)
                                        if(opponent_first):
                                            brd = brd[::-1]
                                        connection.send(str.encode('\n\n{}\nYou played {}\n'.format(brd, mv)))
                                        break
                                except:
                                    pass
                                connection.send(str.encode('\nError, try again\n'))
                            f = open(gameName, 'w')
                            f.write(str(mv) + '\n' + b.fen())
                            f.close()
                            time.sleep(2)
                        else:
                            while(True):
                                time.sleep(1)
                                if(opponent not in [i[:-1] for i in open('names.txt', 'r').readlines()]):
                                    os.remove(gameName)
                                    connection.send(str.encode('\n{} has left the game.\n'.format(opponent)))
                                    break
                                if(not os.path.getsize(gameName) == 0):
                                    f = open(gameName,'r')
                                    lines = f.readlines()
                                    mv = lines[0][:-1]
                                    b.set_fen(lines[1])
                                    f.close()
                                    f = open(gameName, 'w')
                                    f.close()
                                    brd = str(b)
                                    if(opponent_first):
                                        brd = brd[::-1]
                                    connection.send(str.encode('\n\n{}\n\n{} played {}\n'.format(brd, opponent, mv)))
                                    break
                            if(opponent not in [i[:-1] for i in open('names.txt', 'r').readlines()]):
                                break
                        turn = not turn
        except:
            break
    print('Closed connection to: ' + addy)
    names = [i[:-1] for i in open("names.txt", 'r').readlines()]
    names.remove(name)
    f = open("names.txt", 'w')
    for i in names:
        f.write(i + '\n')
    f.close()
    connection.close()

while True:
    Client, address = ServerSocket.accept()
    addy = address[0] + ':' + str(address[1])
    print('Connected to: ' + addy)
    start_new_thread(client_thread, (Client, addy,))
ServerSocket.close()
