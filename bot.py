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
        # Add a new user if they don't already exist
        if username not in self.users:
            self.users[username] = User(username)

    def remove_user(self, username):
        # Remove a user if they exist
        if username in self.users:
            del self.users[username]

    def update_user(self, username, balance=None, slap_count=None, slapped=None):
        # Update user attributes if they exist
        if username in self.users:
            if balance is not None:
                self.users[username].balance = balance
            if slap_count is not None:
                self.users[username].slap_count = slap_count
            if slapped is not None:
                self.users[username].slapped = slapped

    def get_user(self, username):
        # Retrieve a user object
        return self.users.get(username)

    def get_all_users(self):
        # Get a set of all usernames
        return set(self.users.keys())

    def change_username(self, old_username, new_username):
        # Change a user's username
        if old_username in self.users:
            user = self.users[old_username]
            user.username = new_username
            self.users[new_username] = user
            del self.users[old_username]

    def get_leaderboard(self):
        # Return users sorted by balance in descending order
        return sorted(self.users.values(), key=lambda x: x.balance, reverse=True)

class Roulette:
    def __init__(self):
        # Initialize roulette numbers and colors
        self.numbers = list(range(37))
        self.colors = ['green'] + ['red', 'black'] * 18

    def is_odd(self, n):
        # Check if a number is odd
        return n % 2 != 0

    def get_dozen(self, n):
        # Determine which dozen the number falls into
        if 1 <= n <= 12:
            return "1-12"
        elif 13 <= n <= 24:
            return "13-24"
        elif 25 <= n <= 36:
            return "25-36"
        else:
            return None

    def get_range(self, n):
        # Determine which range the number falls into
        if 1 <= n <= 18:
            return "1-18"
        elif 19 <= n <= 36:
            return "19-36"
        else:
            return None

    def play(self, amount, bet):
        # Simulate a roulette spin
        result = random.choice(self.numbers)
        color = self.colors[result]
        is_result_odd = self.is_odd(result)
        dozen = self.get_dozen(result)
        number_range = self.get_range(result)
        
        win = False
        winnings = 0
        
        # Determine if the bet is a winning bet
        if bet in ['red', 'black']:
            if bet == color:
                win = True
                winnings = amount * 2
        elif bet in ['odd', 'even']:
            if (bet == 'odd' and is_result_odd) or (bet == 'even' and not is_result_odd):
                win = True
                winnings = amount * 2
        elif bet in ['1-12', '13-24', '25-36']:
            if bet == dozen:
                win = True
                winnings = amount * 3
        elif bet in ['1-18', '19-36']:
            if bet == number_range:
                win = True
                winnings = amount * 2
        elif bet.isdigit():
            if int(bet) == result:
                win = True
                winnings = amount * 36
        
        return result, color, win, winnings

class Bot:
    def __init__(self, host, port, channel, nick):
        # Initialize bot with connection details
        self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.users = Users()
        self.roulette = Roulette()
        self.host = host
        self.port = port
        self.channel = channel
        self.nick = nick
        self.running = True

    def print_data(self, direction, data):
        # Print data for debugging
        print(f"{direction}: {data}")

    def send_data(self, data):
        # Send data to the IRC server
        self.print_data("SENT", data)
        self.irc.send(data.encode())

    def receive_data(self):
        # Receive data from the IRC server
        data = self.irc.recv(2048).decode("utf-8", errors="ignore").strip("\r\n")
        self.print_data("RECEIVED", data)
        return data

    def getFunFacts(self):
        # Get a random fun fact
        return random.choice(self.turnFunFactFileIntoList())

    def turnFunFactFileIntoList(self):
        # Read fun facts from a file
        with open('./funfacts.txt') as f:
            lines = f.read().splitlines()
        return lines

    def show_commands(self):
        # Display available bot commands
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

    def get_bal(self, username):
        # Get a user's balance
        user = self.users.get_user(username)
        return user.balance if user else 0

    def update_bal(self, username, amount):
        # Update a user's balance
        user = self.users.get_user(username)
        if user:
            self.users.update_user(username, balance=user.balance + amount)

    def handle_ping(self, resp):
        # Respond to server PING messages
        self.send_data(f"PONG {resp.split()[1]}\r\n")

    def process_user_list(self, line):
        # Process the user list from the server
        user_list = line.split(':')[-1].strip().split()
        for username in user_list:
            self.users.add_user(username)

    def handle_user_join(self, line):
        # Handle a user joining the channel
        username = line.split('!')[0][1:]
        self.users.add_user(username)
        self.send_data(f"NAMES {self.channel}\r\n")

    def handle_user_leave(self, line):
        # Handle a user leaving the channel
        username = line.split('!')[0][1:]
        self.users.remove_user(username)

    def handle_nick_change(self, line):
        # Handle a user changing their nickname
        old_username = line.split('!')[0][1:]
        new_username = line.split(':')[-1].strip()
        self.users.change_username(old_username, new_username)

    def proccess_privmsg(self, resp):
        # Process private messages
        parts = resp.split(' ', 3)
        username = parts[0].split('!')[0][1:]
        target = parts[2]
        msg = parts[3][1:]

        # Handle different types of messages
        if target == self.nick:
            fact = self.getFunFacts()
            self.send_data(f"PRIVMSG {username} :{fact}\r\n")
        elif "!" in msg:
            if "!hello" in msg:
                self.send_data(f"PRIVMSG {self.channel} :Hello {username}!\r\n")
            elif "!slap" in msg:
                return self.handle_slap(username, msg)
            elif "!roulette" in msg:
                self.handle_roulette(username, msg)
            elif "!work" in msg:
                self.handle_work(username)
            elif "!bal" in msg:
                self.handle_bal(username, msg)
            else:
                cmds = self.show_commands()
                for cmd in cmds.split('\n'):
                    self.send_data(f"PRIVMSG {self.channel} :{cmd}\r\n")
        return False

    def handle_slap(self, username, msg):
        # Handle the slap command
        parts = msg.split()
        if len(parts) == 2:
            victim = parts[1]
            if victim == self.nick:
                user = self.users.get_user(username)
                user.slap_count += 1
                if user.slap_count == 1:
                    self.send_data(f"PRIVMSG {self.channel} :Really, {username}? You had the nerve to slap me? Fine, but don't push your luck!\r\n")
                elif user.slap_count == 2:
                    self.send_data(f"PRIVMSG {self.channel} :That's it, {username}! I'm furious! One more slap and you'll regret it! Consider yourself warned!\r\n")
                else:
                    self.send_data(f"KICK {self.channel} {username} :That's it! I've warned you enough, {username}! You crossed the line, and now you're out!\r\n")
                    user.slap_count = 0
                self.users.update_user(username, slapped=True)
                # Check if all users have slapped the bot
                if all(self.users.get_user(u).slapped for u in self.users.get_all_users() if u != self.nick):
                    self.send_data(f"PRIVMSG {self.channel} :Seriously?! Every single one of you? After everything I've done for this channel, this is how you treat me?\r\n")
                    self.send_data(f"PART {self.channel} :Fine! I'm leaving. Clearly, no one cares about me here. Goodbye forever. :'-( \r\n")
                    return True  # Signal to main loop to exit
            elif victim in self.users.get_all_users():
                self.send_data(f"PRIVMSG {self.channel} :*slaps {victim} with a trout*\r\n")
            else:
                self.send_data(f"PRIVMSG {self.channel} :Can't slap {victim}, they're not here.\r\n")
        else:
            # Slap a random user if no specific victim
            victims = list(self.users.get_all_users())
            victims.remove(self.nick)
            victims.remove(username)
            if len(victims) > 0:
                victim = random.choice(victims)
                self.send_data(f"PRIVMSG {self.channel} :*slaps {victim} with a trout*\r\n")
            else:
                self.send_data(f"PRIVMSG {self.channel} :No one to slap :(\r\n")
        return False  # Continue normal operation

    def handle_roulette(self, username, msg):
        # Handle the roulette command
        parts = msg.split()
        if len(parts) == 3:
            amt_str = parts[1]
            bet = parts[2]
                        
            if amt_str.isdigit() and int(amt_str) > 0:
                amt = int(amt_str)
                bal = self.get_bal(username)
                            
                if amt > bal:
                    self.send_data(f"PRIVMSG {self.channel} :Sorry {username}, you only have ${bal}. Can't bet ${amt}.\r\n")
                else:
                    self.send_data(f"PRIVMSG {self.channel} :Spinning the wheel...\r\n")
                    time.sleep(4)
                    result, color, win, winnings = self.roulette.play(amt, bet)
                    self.send_data(f"PRIVMSG {self.channel} :It's {result} {color}!\r\n")
                                
                    if win:
                        self.update_bal(username, winnings - amt)
                        self.send_data(f"PRIVMSG {self.channel} :Congrats {username}! You won ${winnings}!\r\n")
                    else:
                        self.update_bal(username, -amt)
                        self.send_data(f"PRIVMSG {self.channel} :Tough luck {username}. You lost ${amt}.\r\n")
                                
                    new_bal = self.get_bal(username)
                    self.send_data(f"PRIVMSG {self.channel} :{username}, your balance: ${new_bal}.\r\n")
            else:
                self.send_data(f"PRIVMSG {self.channel} :Invalid bet. Use a positive number.\r\n")
        else:
            self.send_data(f"PRIVMSG {self.channel} :Wrong format. Use: !roulette <amount> <bet>\r\n")
            self.send_data(f"PRIVMSG {self.channel} :Bets: red/black, odd/even, 1-12/13-24/25-36, 1-18/19-36, or 0-36\r\n")

    def handle_work(self, username):
        # Handle the work command
        pay = random.randint(100, 900)
        self.update_bal(username, pay)
        new_bal = self.get_bal(username)
        self.send_data(f"PRIVMSG {self.channel} :{username}, worked hard and got ${pay}!\r\n")
        self.send_data(f"PRIVMSG {self.channel} :{username}, Your balance: ${new_bal}.\r\n")

    def handle_bal(self, username, msg):
        # Handle the balance check command
        parts = msg.split()
        if len(parts) == 1:
            bal = self.get_bal(username)
            self.send_data(f"PRIVMSG {self.channel} :{username}, Your balance: ${bal}.\r\n")
        elif len(parts) == 2 and parts[1] == "-lb":
            leaderboard = self.users.get_leaderboard()
            self.send_data(f"PRIVMSG {self.channel} :Leaderboard:\r\n")
            for i, user in enumerate(leaderboard[:10], 1):
                self.send_data(f"PRIVMSG {self.channel} :{i}. {user.username}: ${user.balance}\r\n")
        else:
            self.send_data(f"PRIVMSG {self.channel} :Invalid command. Use !bal or !bal -lb\r\n")

    def handle_nick_error(self):
        # Handle nickname errors and ask for a new one
        while True:
            new_nick = input("Nickname is already in use. Please enter a new nickname for bot: ")
            self.send_data(f"NICK {new_nick}\r\n")
            
            # Wait for server response
            while True:
                resp = self.receive_data()
                if "433" in resp or "432" in resp:  # Nickname is still in use or erroneous
                    print(f"Nickname '{new_nick}' is invalid or already in use. Please try again.")
                    break
                else: 
                    self.nick = new_nick
                    return
    
    def run(self):
        # Main function to run the IRC bot
        try:
            # Connect to the IRC server
            self.irc.connect((self.host, self.port))
        except Exception as e:
            print(f"Error: Failed to connect to {self.host}:{self.port}. {str(e)}")
            return

        # Send initial NICK command
        self.send_data(f"NICK {self.nick}\r\n")

        nick_accepted = False
        try:
            while self.running:
                try:
                    resp = self.receive_data()
                    if not resp:
                        print("Connection closed by the server.")
                        break

                    if resp.startswith("PING"):
                        self.handle_ping(resp)

                    if "PRIVMSG" in resp:
                        if self.proccess_privmsg(resp):
                            break  # Exit if the bot was slapped by everyone
                    else:
                        lines = resp.splitlines()
                        for line in lines:
                            if "433" in line or "432" in line:  # Nickname is already in use or erroneous
                                self.handle_nick_error()
                            elif not nick_accepted and "001" not in line:
                                self.send_data(f"USER {self.nick} 0 * :{self.nick}\r\n")
                                nick_accepted = True
                            elif "001" in line:  # Welcome message, we're connected
                                self.send_data(f"JOIN {self.channel}\r\n")
                            elif "JOIN" in line:
                                self.handle_user_join(line)
                            elif "PART" in line or "QUIT" in line:
                                self.handle_user_leave(line)
                                self.send_data(f"NAMES {self.channel}\r\n")
                            elif "353" in line and self.channel in line:  # NAMES reply
                                self.process_user_list(line)
                            elif "NICK" in line:
                                self.handle_nick_change(line)
                                self.send_data(f"NAMES {self.channel}\r\n")

                except socket.error as e:
                    print(f"Socket error occurred: {e}")
                    break
                except Exception as e:
                    print(f"An error occurred: {e}")
                    break
        except KeyboardInterrupt:
            print("\nBot is shutting down...")
        finally:
            self.send_data(f"QUIT :Bot is shutting down\r\n")
            self.irc.close()  # Ensuring the socket is closed when exiting
            print("Connection closed.")

def parse_arguments():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="IRC Bot")
    parser.add_argument("--host", default="::", help="Server to connect to")
    parser.add_argument("--port", type=int, default=6667, help="Port to connect to")
    parser.add_argument("--name", default="CoolBot", help="Nickname for the bot")
    parser.add_argument("--channel", default="#test", help="Channel to join")
    return parser.parse_args()

def main():
    # Main entry point for the bot
    args = parse_arguments()
    bot = Bot(args.host, args.port, args.channel, args.name)
    bot.run()

if __name__ == "__main__":
    main()
