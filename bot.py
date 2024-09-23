import socket
import random
import time
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="IRC Bot")
parser.add_argument("--host", default="::", help="Server to connect to")
parser.add_argument("--port", type=int, default=6667, help="Port to connect to")
parser.add_argument("--name", default="CoolBot", help="Nickname for the bot")
parser.add_argument("--channel", default="#test", help="Channel to join")
args = parser.parse_args()

# Bot config
SERVER = args.host
PORT = args.port
CHANNEL = args.channel
NICK = args.name

irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
irc.connect((SERVER, PORT))

irc.send(f"NICK {NICK}\r\n".encode())
irc.send(f"USER {NICK} 0 * :{NICK}\r\n".encode())
irc.send(f"JOIN {CHANNEL}\r\n".encode())

users = set()
balances = {}

# Fun facts
facts = [
    "Flamingos can drink boiling water.",
    "Cows moo with regional accents.",
    "The shortest war lasted 38 min.",
    "Bananas are berries.",
    "The moon has quakes.",
    "Octopuses have 3 hearts.",
    "A jiffy is 1/100th of a sec.",
    "Oldest tree is 5000+ years old.",
    "Cows have besties.",
    "Koala prints look human-like.",
    "Venus day > Venus year."
]

# Roulette stuff
numbers = list(range(37))
colors = ['green'] + ['red', 'black'] * 18

def is_odd(n):
    return n % 2 != 0

def get_dozen(n):
    if n >= 1 and n <= 12:
        return "1-12"
    elif n >= 13 and n <= 24:
        return "13-24"
    elif n >= 25 and n <= 36:
        return "25-36"
    else:
        return None

def get_range(n):
    if n >= 1 and n <= 18:
        return "1-18"
    elif n >= 19 and n <= 36:
        return "19-36"
    else:
        return None

def play_roulette(amount, bet):
    result = random.choice(numbers)
    color = colors[result]
    is_result_odd = is_odd(result)
    dozen = get_dozen(result)
    number_range = get_range(result)
    
    win = False
    winnings = 0
    
    if bet == 'red' or bet == 'black':
        if bet == color:
            win = True
            winnings = amount * 2
    elif bet == 'odd' or bet == 'even':
        if (bet == 'odd' and is_result_odd) or (bet == 'even' and not is_result_odd):
            win = True
            winnings = amount * 2
    elif bet == '1-12' or bet == '13-24' or bet == '25-36':
        if bet == dozen:
            win = True
            winnings = amount * 3
    elif bet == '1-18' or bet == '19-36':
        if bet == number_range:
            win = True
            winnings = amount * 2
    elif bet.isdigit():
        if int(bet) == result:
            win = True
            winnings = amount * 36
    
    return result, color, win, winnings

def show_commands():
    cmds = [
        "Commands:",
        "!hello - Say hello",
        "!slap <user> - Slap someone",
        "!roulette <amount> <bet> - Gamble",
        "!work - Get money",
        "!bal - Check balance",
        "Roulette bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36"
    ]
    return "\n".join(cmds)

def get_bal(user):
    if user not in balances:
        balances[user] = 1000
    return balances[user]

def update_bal(user, amount):
    if user not in balances:
        balances[user] = 1000
    balances[user] += amount

while True:
    try:
        resp = irc.recv(2048).decode("utf-8", errors="ignore").strip("\r\n")
        print(resp)

        if resp.startswith("PING"):
            irc.send(f"PONG {resp.split()[1]}\r\n".encode())

        lines = resp.splitlines()

        for line in lines:
            if "353" in line and CHANNEL in line:
                user_list = line.split(':')[-1].strip().split()
                for user in user_list:
                    users.add(user)
            elif "JOIN" in line:
                user = line.split('!')[0][1:]
                users.add(user)
            elif "PART" in line or "QUIT" in line:
                user = line.split('!')[0][1:]
                if user in users:
                    users.remove(user)

        if "PRIVMSG" in resp:
            parts = resp.split(' ', 3)
            user = parts[0].split('!')[0][1:]
            target = parts[2]
            msg = parts[3][1:]

            if target == NICK:
                fact = random.choice(facts)
                irc.send(f"PRIVMSG {user} :{fact}\r\n".encode())

            elif msg == "!":
                cmds = show_commands()
                for cmd in cmds.split('\n'):
                    irc.send(f"PRIVMSG {CHANNEL} :{cmd}\r\n".encode())

            elif msg == "!hello":
                irc.send(f"PRIVMSG {CHANNEL} :Hello {user}!\r\n".encode())

            elif msg.startswith("!slap"):
                parts = msg.split()
                if len(parts) == 2:
                    victim = parts[1]
                    if victim != NICK and victim in users:
                        irc.send(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n".encode())
                    elif victim == NICK:
                        irc.send(f"PRIVMSG {CHANNEL} :*slaps {user} back with a tuna* Take that!\r\n".encode())
                    else:
                        irc.send(f"PRIVMSG {CHANNEL} :Can't slap {victim}, they're not here.\r\n".encode())
                else:
                    victims = list(users)
                    victims.remove(NICK)
                    victims.remove(user)
                    if len(victims) > 0:
                        victim = random.choice(victims)
                        irc.send(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n".encode())
                    else:
                        irc.send(f"PRIVMSG {CHANNEL} :No one to slap :(\r\n".encode())

            elif msg.startswith("!roulette"):
                parts = msg.split()
                if len(parts) == 3:
                    amt_str = parts[1]
                    bet = parts[2]
                    
                    if amt_str.isdigit() and int(amt_str) > 0:
                        amt = int(amt_str)
                        bal = get_bal(user)
                        
                        if amt > bal:
                            irc.send(f"PRIVMSG {CHANNEL} :Sorry {user}, you only have ${bal}. Can't bet ${amt}.\r\n".encode())
                        else:
                            irc.send(f"PRIVMSG {CHANNEL} :Spinning the wheel...\r\n".encode())
                            time.sleep(4)
                            result, color, win, winnings = play_roulette(amt, bet)
                            irc.send(f"PRIVMSG {CHANNEL} :It's {result} {color}!\r\n".encode())
                            
                            if win:
                                update_bal(user, winnings - amt)
                                irc.send(f"PRIVMSG {CHANNEL} :Congrats {user}! You won ${winnings}!\r\n".encode())
                            else:
                                update_bal(user, -amt)
                                irc.send(f"PRIVMSG {CHANNEL} :Tough luck {user}. You lost ${amt}.\r\n".encode())
                            
                            new_bal = get_bal(user)
                            irc.send(f"PRIVMSG {CHANNEL} :{user}, your balance: ${new_bal}.\r\n".encode())
                    else:
                        irc.send(f"PRIVMSG {CHANNEL} :Invalid bet. Use a positive number.\r\n".encode())
                else:
                    irc.send(f"PRIVMSG {CHANNEL} :Wrong format. Use: !roulette <amount> <bet>\r\n".encode())
                    irc.send(f"PRIVMSG {CHANNEL} :Bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36\r\n".encode())

            elif msg == "!work":
                pay = random.randint(100, 900)
                update_bal(user, pay)
                irc.send(f"PRIVMSG {CHANNEL} :{user} worked hard and got ${pay}!\r\n".encode())
                new_bal = get_bal(user)
                irc.send(f"PRIVMSG {CHANNEL} :Your balance: ${new_bal}.\r\n".encode())

            elif msg == "!bal":
                bal = get_bal(user)
                irc.send(f"PRIVMSG {CHANNEL} :{user}, you have ${bal}.\r\n".encode())
    except KeyboardInterrupt:
        print("Bot is shutting down...")
        break
    except Exception as e:
        print(f"An error occurred: {e}")
        continue
