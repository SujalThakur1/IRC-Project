# Import necessary modules
import socket
import random
import time
import argparse
import json

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="IRC Bot")
    parser.add_argument("--host", default="::", help="Server to connect to")
    parser.add_argument("--port", type=int, default=6667, help="Port to connect to")
    parser.add_argument("--name", default="CoolBot", help="Nickname for the bot")
    parser.add_argument("--channel", default="#test", help="Channel to join")
    args = parser.parse_args()
    return args

# Function to get server configuration from command-line arguments
def get_server_config():
    args = parse_arguments()
    return args.host, args.port, args.channel, args.name

# Create IPv6 socket for IRC connection
irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

# Function to print sent/received data for debugging
def print_data(direction, data):
    print(f"{direction}: {data}")

# Function to send data to the IRC server
def send_data(data):
    print_data("SENT", data)
    irc.send(data.encode())

# Function to receive data from the IRC server
def receive_data():
    data = irc.recv(2048).decode("utf-8", errors="ignore").strip("\r\n")
    print_data("RECEIVED", data)
    return data

# Set to store connected users
users = set()

# Dictionary to store user balances
balances = {}

# List of random facts for the bot to share
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

# Roulette game setup
numbers = list(range(37))
colors = ['green'] + ['red', 'black'] * 18

# Function to check if a number is odd
def is_odd(n):
    return n % 2 != 0

# Function to get the dozen for a roulette number
def get_dozen(n):
    if n >= 1 and n <= 12:
        return "1-12"
    elif n >= 13 and n <= 24:
        return "13-24"
    elif n >= 25 and n <= 36:
        return "25-36"
    else:
        return None

# Function to get the range for a roulette number
def get_range(n):
    if n >= 1 and n <= 18:
        return "1-18"
    elif n >= 19 and n <= 36:
        return "19-36"
    else:
        return None

# Function to simulate a roulette game
def play_roulette(amount, bet):
    result = random.choice(numbers)
    color = colors[result]
    is_result_odd = is_odd(result)
    dozen = get_dozen(result)
    number_range = get_range(result)
    
    win = False
    winnings = 0
    
    # Complex logic to determine if the bet wins
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

# Function to display available bot commands
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

# Function to get a user's balance
def get_bal(user):
    if user not in balances:
        balances[user] = 1000
    return balances[user]

# Function to save balances to a file
def save_info(balances):
    with open("bal.txt", "w") as file:
        json.dump(balances, file)

# Function to update a user's balance
def update_bal(user, amount):
    if user not in balances:
        balances[user] = 1000
    balances[user] += amount
    save_info(balances)

# Function to load balances from a file
def load_info():
    global balances
    try:
        # Load balances from file
        with open ("bal.txt", "r") as file:
            balances = json.load(file)
    except FileNotFoundError:
        balances = {}

# Function to handle PING messages from the server
def handle_ping(resp):
    send_data(f"PONG {resp.split()[1]}\r\n")

# Function to process the user list received from the server
def proccess_user_list(line):
    # Parse the user list
    user_list = line.split(':')[-1].strip().split()
    for user in user_list:
        users.add(user)

# Function to handle a user joining the channel
def handle_user_join(line):
    # Get the user that joined
    user = line.split('!')[0][1:]
    users.add(user)

# Function to handle a user leaving the channel
def handle_user_leave(line):
    # Get the user that left
    user = line.split('!')[0][1:]
    if user in users:
        users.remove(user)

# Function to process private messages
def proccess_privmsg(resp, NICK, CHANNEL):
    # Parse the message
    parts = resp.split(' ', 3)
    # Get the user, target, and message
    user = parts[0].split('!')[0][1:]
    target = parts[2]
    msg = parts[3][1:]

    # Handle different types of messages
    if target == NICK:
        fact = random.choice(facts)
        send_data(f"PRIVMSG {user} :{fact}\r\n")
    elif msg == "!":
        cmds = show_commands()
        for cmd in cmds.split('\n'):
            send_data(f"PRIVMSG {CHANNEL} :{cmd}\r\n")
    elif msg == "!hello":
        send_data(f"PRIVMSG {CHANNEL} :Hello {user}!\r\n")
    elif msg.startswith("!slap"):
        handle_slap(user, msg, NICK, CHANNEL)
    elif msg.startswith("!roulette"):
        handle_roulette(user, msg, CHANNEL)
    elif msg == "!work":
        handle_work(user, CHANNEL)
    elif msg == "!bal":
        handle_bal(user, CHANNEL)

# Function to handle the slap command
def handle_slap(user, msg, NICK, CHANNEL):
    parts = msg.split()
    if len(parts) == 2:
        victim = parts[1]
        if victim != NICK and victim in users:
            send_data(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n")
        elif victim == NICK:
            send_data(f"PRIVMSG {CHANNEL} :*slaps {user} back with a tuna* Take that!\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :Can't slap {victim}, they're not here.\r\n")
    else:
        # Slap a random user if no specific victim
        victims = list(users)
        victims.remove(NICK)
        victims.remove(user)
        if len(victims) > 0:
            victim = random.choice(victims)
            send_data(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :No one to slap :(\r\n")

# Function to handle the roulette command
def handle_roulette(user, msg, CHANNEL):
    parts = msg.split()
    if len(parts) == 3:
        amt_str = parts[1]
        bet = parts[2]
                    
        if amt_str.isdigit() and int(amt_str) > 0:
            amt = int(amt_str)
            bal = get_bal(user)
                        
            if amt > bal:
                send_data(f"PRIVMSG {CHANNEL} :Sorry {user}, you only have ${bal}. Can't bet ${amt}.\r\n")
            else:
                send_data(f"PRIVMSG {CHANNEL} :Spinning the wheel...\r\n")
                time.sleep(4)
                result, color, win, winnings = play_roulette(amt, bet)
                send_data(f"PRIVMSG {CHANNEL} :It's {result} {color}!\r\n")
                            
                if win:
                    update_bal(user, winnings - amt)
                    send_data(f"PRIVMSG {CHANNEL} :Congrats {user}! You won ${winnings}!\r\n")
                else:
                    update_bal(user, -amt)
                    send_data(f"PRIVMSG {CHANNEL} :Tough luck {user}. You lost ${amt}.\r\n")
                            
                new_bal = get_bal(user)
                send_data(f"PRIVMSG {CHANNEL} :{user}, your balance: ${new_bal}.\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :Invalid bet. Use a positive number.\r\n")
    else:
        send_data(f"PRIVMSG {CHANNEL} :Wrong format. Use: !roulette <amount> <bet>\r\n")
        send_data(f"PRIVMSG {CHANNEL} :Bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36\r\n")

# Function to handle the work command
def handle_work(user, CHANNEL):
    # Pay the user for working
    pay = random.randint(100, 900)
    update_bal(user, pay)
    new_bal = get_bal(user)
    send_data(f"PRIVMSG {CHANNEL} :{user}, worked hard and got ${pay}!\r\n")
    send_data(f"PRIVMSG {CHANNEL} :{user}, Your balance: ${new_bal}.\r\n")

# Function to handle the balance check command
def handle_bal(user, CHANNEL):
    bal = get_bal(user)
    send_data(f"PRIVMSG {CHANNEL} :{user}, Your balance: ${bal}.\r\n")

# Main function to run the IRC bot
def main():
    SERVER, PORT, CHANNEL, NICK = get_server_config()
    
    load_info()

    # Connect to the IRC server
    irc.connect((SERVER, PORT))

    # Send initial IRC commands
    send_data(f"NICK {NICK}\r\n")
    send_data(f"USER {NICK} 0 * :{NICK}\r\n")
    send_data(f"JOIN {CHANNEL}\r\n")

    try:
        while True:
            try:
                resp = receive_data()
                if not resp:
                    print("Connection closed by the server.")
                    break

                if resp.startswith("PING"):
                    handle_ping(resp)

                lines = resp.splitlines()

                for line in lines:
                    if "353" in line and CHANNEL in line:
                        proccess_user_list(line)
                    elif "JOIN" in line:
                        handle_user_join(line)
                    elif "PART" in line or "QUIT" in line:
                        handle_user_leave(line)

                if "PRIVMSG" in resp:
                    proccess_privmsg(resp, NICK, CHANNEL)

            except socket.error as e:
                print(f"Socket error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
    except KeyboardInterrupt:
        print("Bot is shutting down...")
    finally:
        irc.close()  # Ensuring the socket is closed when exiting
        print("Connection closed.")

# Entry point of the script
if __name__ == "__main__":
    main()
