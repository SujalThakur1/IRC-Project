# Import necessary modules
import socket
import random
import time
import argparse

# User class to represent individual users
class User:
    def __init__(self, username, balance=1000, slap_count=0, slapped=False):
        self.username = username
        self.balance = balance
        self.slap_count = slap_count
        self.slapped = slapped

# Users class to manage all users
class Users:
    def __init__(self):
        self.users = {}

    def add_user(self, username):
        if username not in self.users:
            self.users[username] = User(username)

    def remove_user(self, username):
        if username in self.users:
            del self.users[username]

    def update_user(self, username, balance=None, slap_count=None, slapped=None):
        if username in self.users:
            if balance is not None:
                self.users[username].balance = balance
            if slap_count is not None:
                self.users[username].slap_count = slap_count
            if slapped is not None:
                self.users[username].slapped = slapped

    def get_user(self, username):
        return self.users.get(username)

    def get_all_users(self):
        return set(self.users.keys())

    def change_username(self, old_username, new_username):
        if old_username in self.users:
            user = self.users[old_username]
            user.username = new_username
            self.users[new_username] = user
            del self.users[old_username]

    def get_leaderboard(self):
        return sorted(self.users.values(), key=lambda x: x.balance, reverse=True)

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

# Initialize Users instance
users = Users()

# Function that gets fun facts from an api
def getFunFacts():
    return random.choice(turnFunFactFileIntoList())

def turnFunFactFileIntoList():
    with open('./funfacts.txt') as f:
        lines = f.read().splitlines()
    return lines

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
        "!bal -lb - Show leaderboard",
        "Roulette bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36"
    ]
    return "\n".join(cmds)

# Function to get a user's balance
def get_bal(username):
    user = users.get_user(username)
    return user.balance if user else 0

# Function to update a user's balance
def update_bal(username, amount):
    user = users.get_user(username)
    if user:
        users.update_user(username, balance=user.balance + amount)

# Function to handle PING messages from the server
def handle_ping(resp):
    send_data(f"PONG {resp.split()[1]}\r\n")

# Function to process the user list received from the server
def process_user_list(line):
    # Parse the user list
    user_list = line.split(':')[-1].strip().split()
    for username in user_list:
        users.add_user(username)

# Function to handle a user joining the channel
def handle_user_join(line, CHANNEL):
    # Get the user that joined
    username = line.split('!')[0][1:]
    users.add_user(username)
    # Request updated user list
    send_data(f"NAMES {CHANNEL}\r\n")

# Function to handle a user leaving the channel
def handle_user_leave(line):
    # Get the user that left
    username = line.split('!')[0][1:]
    users.remove_user(username)

# Function to handle a user changing their nickname
def handle_nick_change(line):
    # Get the old and new usernames
    old_username = line.split('!')[0][1:]
    new_username = line.split(':')[-1].strip()
    users.change_username(old_username, new_username)

# Function to process private messages
def proccess_privmsg(resp, NICK, CHANNEL):
    # Parse the message
    parts = resp.split(' ', 3)
    # Get the user, target, and message
    username = parts[0].split('!')[0][1:]
    target = parts[2]
    msg = parts[3][1:]

    # Handle different types of messages
    if target == NICK:
        fact = getFunFacts()
        send_data(f"PRIVMSG {username} :{fact}\r\n")
    elif msg == "!":
        cmds = show_commands()
        for cmd in cmds.split('\n'):
            send_data(f"PRIVMSG {CHANNEL} :{cmd}\r\n")
    elif msg == "!hello":
        send_data(f"PRIVMSG {CHANNEL} :Hello {username}!\r\n")
    elif msg.startswith("!slap"):
        return handle_slap(username, msg, NICK, CHANNEL)
    elif msg.startswith("!roulette"):
        handle_roulette(username, msg, CHANNEL)
    elif msg == "!work":
        handle_work(username, CHANNEL)
    elif msg.startswith("!bal"):
        handle_bal(username, msg, CHANNEL)
    return False

# Function to handle the slap command
def handle_slap(username, msg, NICK, CHANNEL):
    parts = msg.split()
    if len(parts) == 2:
        victim = parts[1]
        if victim == NICK:
            user = users.get_user(username)
            user.slap_count += 1
            if user.slap_count == 1:
                send_data(f"PRIVMSG {CHANNEL} :Really, {username}? You had the nerve to slap me? Fine, but don't push your luck!\r\n")
            elif user.slap_count == 2:
                send_data(f"PRIVMSG {CHANNEL} :That's it, {username}! I'm furious! One more slap and you'll regret it! Consider yourself warned!\r\n")
            else:
                send_data(f"KICK {CHANNEL} {username} :That's it! I've warned you enough, {username}! You crossed the line, and now you're out!\r\n")
                user.slap_count = 0
            users.update_user(username, slapped=True)
            # Check if all users have slapped the bot
            if all(users.get_user(u).slapped for u in users.get_all_users() if u != NICK):
                send_data(f"PRIVMSG {CHANNEL} :Seriously?! Every single one of you? After everything I've done for this channel, this is how you treat me?\r\n")
                send_data(f"PART {CHANNEL} :Fine! I'm leaving. Clearly, no one cares about me here. Goodbye forever. :'-( \r\n")
                return True  # Signal to main loop to exit
        elif victim in users.get_all_users():
            send_data(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :Can't slap {victim}, they're not here.\r\n")
    else:
        # Slap a random user if no specific victim
        victims = list(users.get_all_users())
        victims.remove(NICK)
        victims.remove(username)
        if len(victims) > 0:
            victim = random.choice(victims)
            send_data(f"PRIVMSG {CHANNEL} :*slaps {victim} with a trout*\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :No one to slap :(\r\n")
    return False  # Continue normal operation

# Function to handle the roulette command
def handle_roulette(username, msg, CHANNEL):
    parts = msg.split()
    if len(parts) == 3:
        amt_str = parts[1]
        bet = parts[2]
                    
        if amt_str.isdigit() and int(amt_str) > 0:
            amt = int(amt_str)
            bal = get_bal(username)
                        
            if amt > bal:
                send_data(f"PRIVMSG {CHANNEL} :Sorry {username}, you only have ${bal}. Can't bet ${amt}.\r\n")
            else:
                send_data(f"PRIVMSG {CHANNEL} :Spinning the wheel...\r\n")
                time.sleep(4)
                result, color, win, winnings = play_roulette(amt, bet)
                send_data(f"PRIVMSG {CHANNEL} :It's {result} {color}!\r\n")
                            
                if win:
                    update_bal(username, winnings - amt)
                    send_data(f"PRIVMSG {CHANNEL} :Congrats {username}! You won ${winnings}!\r\n")
                else:
                    update_bal(username, -amt)
                    send_data(f"PRIVMSG {CHANNEL} :Tough luck {username}. You lost ${amt}.\r\n")
                            
                new_bal = get_bal(username)
                send_data(f"PRIVMSG {CHANNEL} :{username}, your balance: ${new_bal}.\r\n")
        else:
            send_data(f"PRIVMSG {CHANNEL} :Invalid bet. Use a positive number.\r\n")
    else:
        send_data(f"PRIVMSG {CHANNEL} :Wrong format. Use: !roulette <amount> <bet>\r\n")
        send_data(f"PRIVMSG {CHANNEL} :Bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36\r\n")

# Function to handle the work command
def handle_work(username, CHANNEL):
    # Pay the user for working
    pay = random.randint(100, 900)
    update_bal(username, pay)
    new_bal = get_bal(username)
    send_data(f"PRIVMSG {CHANNEL} :{username}, worked hard and got ${pay}!\r\n")
    send_data(f"PRIVMSG {CHANNEL} :{username}, Your balance: ${new_bal}.\r\n")

# Function to handle the balance check command
def handle_bal(username, msg, CHANNEL):
    parts = msg.split()
    if len(parts) == 1:
        bal = get_bal(username)
        send_data(f"PRIVMSG {CHANNEL} :{username}, Your balance: ${bal}.\r\n")
    elif len(parts) == 2 and parts[1] == "-lb":
        leaderboard = users.get_leaderboard()
        send_data(f"PRIVMSG {CHANNEL} :Leaderboard:\r\n")
        for i, user in enumerate(leaderboard[:10], 1):
            send_data(f"PRIVMSG {CHANNEL} :{i}. {user.username}: ${user.balance}\r\n")
    else:
        send_data(f"PRIVMSG {CHANNEL} :Invalid command. Use !bal or !bal -lb\r\n")
# Function to handle nickname errors and ask for a new one
def handle_nick_error(CHANNEL):
    while True:
        new_nick = input("Nickname is already in use. Please enter a new nickname: ")
        send_data(f"NICK {new_nick}\r\n")
        
        # Wait for server response
        while True:
            resp = receive_data()
            if "433" in resp or "432" in resp:  # Nickname is still in use or erroneous
                print(f"Nickname '{new_nick}' is invalid or already in use. Please try again.")
                break
            else: 
                send_data(f"USER {new_nick} 0 * :{new_nick}\r\n")
                return new_nick

# Main function to run the IRC bot
def main():
    SERVER, PORT, CHANNEL, NICK = get_server_config()

    # Connect to the IRC server
    irc.connect((SERVER, PORT))

    # Send initial NICK command
    send_data(f"NICK {NICK}\r\n")

    try:
        while True:
            try:
                resp = receive_data()
                if not resp:
                    print("Connection closed by the server.")
                    break

                if resp.startswith("PING"):
                    handle_ping(resp)

                if "PRIVMSG" in resp:
                    if proccess_privmsg(resp, NICK, CHANNEL):
                        break  # Exit if the bot was slapped by everyone
                else:
                    lines = resp.splitlines()
                    for line in lines:
                        if "433" in line or "432" in line:  # Nickname is already in use or erroneous
                            NICK = handle_nick_error(CHANNEL)
                            print("outside")
                        elif "001" in line:  # Welcome message, we're connected
                            # Send USER command only after successful NICK registration

                            send_data(f"JOIN {CHANNEL}\r\n")
                        elif "JOIN" in line:
                            handle_user_join(line, CHANNEL)
                        elif "PART" in line or "QUIT" in line:
                            handle_user_leave(line)
                            send_data(f"NAMES {CHANNEL}\r\n")
                        elif "353" in line and CHANNEL in line:  # NAMES reply
                            process_user_list(line)
                        elif "NICK" in line:
                            handle_nick_change(line)
                            send_data(f"NAMES {CHANNEL}\r\n")


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
