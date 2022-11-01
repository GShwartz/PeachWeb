from flask import Flask, render_template, request, flash
from datetime import datetime
from termcolor import colored
from threading import Thread
from colorama import init
import os.path
import socket
import psutil
import sys

# Web API
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Local Modules
from Modules import screenshot
from Modules import tasks
from Modules import vital_signs
from Modules import sysinfo
from Modules import freestyle

# Testing ENV
import random
import string

init()


# app = Flask(__name__)
# app.config['SECRET_KEY'] = "SuperSecretKey"
app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates", html=True), name="templates")
templates = Jinja2Templates(directory="templates")

Base = declarative_base()


# noinspection PyMissingConstructor
class Person(Base):
    __tablename__ = 'users'
    pid = Column("id", Integer, primary_key=True)
    firstName = Column("firstname", String)
    email = Column("email", String)
    password = Column("password", String)

    def __init__(self, pid, fName, email, pword):
        self.id = pid
        self.firstName = fName
        self.email = email
        self.password = pword

    def __repr__(self):
        return f"({self.pid}) ({self.firstName}) ({self.email})"


@app.get("/")
async def home():
    return templates.get_template("index")


@app.route('/devices', methods=['GET', 'POST'])
def devices():
    return render_template('devices.html', title='Devices')


@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    print(data)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if len(email) < 4:
            flash('Email must be legit bro.', category='fail')

        elif len(password) < 7:
            flash("Password too short.", category='fail')

    return render_template('login.html', title='LogIn')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Init DB for signup
    ses = sessionmaker(bind=engine)
    Session = ses
    sess = Session()

    if request.method == 'POST':
        email = request.form.get('email')
        emailExists = sess.query(Person).filter_by(email=f"{email}").scalar() is not None

        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if len(email) < 4:
            flash('Email must be legit bro.', category='fail')

        elif emailExists:
            flash('Email exists bro.', category='fail')

        elif len(firstName) < 2:
            flash('Name must be legit bro.', category='fail')

        elif password1 != password2:
            flash("The passwords don't match dude!", category='fail')

        elif len(password1) < 7:
            flash("Password too short.", category='fail')

        else:
            person = Person(1, firstName, email, password2)
            sess.add(person)
            sess.commit()

            flash("Account created!", category='win')
            results = sess.query(Person).all()
            print(results)

            return render_template('about.html', title='About')

    return render_template('signup.html', title='SignUp')


class Server:
    clients = {}
    connections = {}
    connHistory = []
    ips = []
    targets = []
    threads = []

    def __init__(self, serverIP, serverPort, ttl, path, log_path):
        self.serverIp = serverIP
        self.serverPort = serverPort
        self.ttl = ttl
        self.path = path
        self.log_path = log_path
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.serverIp, self.serverPort))
        self.server.listen()

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def reset(self) -> None:
        self.__init__(self.serverIp, self.serverPort, self.ttl, self.path, self.log_path)
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.serverIp, self.serverPort))
        self.server.listen()

    def bytes_to_number(self, b: int) -> int:
        self.logIt_thread(self.log_path, msg=f'Running bytes_to_number({b})...')
        dt = get_date()
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def get_date(self) -> str:
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%m/%d/%Y %H:%M:%S"))

        return dt

    def logIt(self, logfile=None, debug=None, msg='') -> bool:
        dt = self.get_date()
        if debug:
            print(f"{dt}: {msg}")

        if logfile is not None:
            try:
                if not os.path.exists(logfile):
                    with open(logfile, 'w') as lf:
                        lf.write(f"{dt}: {msg}\n")

                    return True

                else:
                    with open(logfile, 'a') as lf:
                        lf.write(f"{dt}: {msg}\n")

                    return True

            except FileExistsError:
                pass

    def logIt_thread(self, log_path=None, debug=False, msg='') -> None:
        self.logit_thread = Thread(target=self.logIt, args=(log_path, debug, msg), name="Log Thread")
        self.logit_thread.start()
        self.threads.append(self.logit_thread)

    def run(self) -> None:
        self.logIt_thread(self.log_path, msg=f'Running run()...')
        self.logIt_thread(self.log_path, msg=f'Calling connect() in new thread...')
        self.connectThread = Thread(target=self.connect, daemon=True, name=f"Connect Thread")
        self.connectThread.start()

        self.logIt_thread(self.log_path, msg=f'Adding thread to threads list...')
        self.threads.append(self.connectThread)
        self.logIt_thread(self.log_path, msg=f'Thread added to threads list.')

    def connect(self) -> None:
        def get_mac_address() -> str:
            self.logIt_thread(self.log_path, msg=f'Waiting for MAC address from {self.ip}...')
            self.mac = self.conn.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'MAC Address: {self.mac}')

            self.logIt_thread(self.log_path, msg=f'Sending confirmation to {self.ip}...')
            self.conn.send('OK'.encode())
            self.logIt_thread(self.log_path, msg=f'Send completed.')

            return self.mac

        def get_hostname() -> str:
            self.logIt_thread(self.log_path, msg=f'Waiting for remote station name...')
            self.ident = self.conn.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'Remote station name: {self.ident}')

            self.logIt_thread(self.log_path, msg=f'Sending Confirmation to {self.ip}...')
            self.conn.send('OK'.encode())
            self.logIt_thread(self.log_path, msg=f'Send completed.')

            return self.ident

        def get_user() -> str:
            self.logIt_thread(self.log_path, msg=f'Waiting for remote station current logged user...')
            self.user = self.conn.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'Remote station user: {self.user}')

            self.logIt_thread(self.log_path, msg=f'Sending Confirmation to {self.ip}...')
            self.conn.send('OK'.encode())
            self.logIt_thread(self.log_path, msg=f'Send completed.')

            return self.user

        def get_client_version() -> str:
            self.logIt_thread(self.log_path, msg=f'Waiting for client version...')
            self.client_version = self.conn.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'Client version: {self.client_version}')

            self.logIt_thread(self.log_path, msg=f'Sending confirmation to {self.ip}...')
            self.conn.send('OK'.encode())
            self.logIt_thread(self.log_path, msg=f'Send completed.')

            return self.client_version

        self.logIt_thread(self.log_path, msg=f'Running connect()...')
        while True:
            self.logIt_thread(self.log_path, msg=f'Accepting connections...')
            self.conn, (self.ip, self.port) = self.server.accept()
            self.logIt_thread(self.log_path, msg=f'Connection from {self.ip} accepted.')

            try:
                # Get MAC Address
                get_mac_address()

                # Get Remote Computer's Name
                get_hostname()

                # Get Current User
                get_user()

                # Get Client Version
                get_client_version()

            except (WindowsError, socket.error) as e:
                self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
                return  # Restart The Loop

            # Update Thread Dict and Connection Lists
            if self.conn not in self.targets and self.ip not in self.ips:
                self.logIt_thread(self.log_path, msg=f'New Connection!')

                # Add Socket Connection To Targets list
                self.logIt_thread(self.log_path, msg=f'Adding {self.conn} to targets list...')
                self.targets.append(self.conn)
                self.logIt_thread(self.log_path, msg=f'targets list updated.')

                # Add IP Address Connection To IPs list
                self.logIt_thread(self.log_path, msg=f'Adding {self.ip} to ips list...')
                self.ips.append(self.ip)
                self.logIt_thread(self.log_path, msg=f'ips list updated.')

                # Set Temp Dict To Update Live Connections List
                self.logIt_thread(self.log_path, msg=f'Adding {self.conn} | {self.ip} to temp live connections dict...')
                self.temp_connection = {self.conn: self.ip}
                self.logIt_thread(self.log_path, msg=f'Temp connections dict updated.')

                # Add Temp Dict To Connections List
                self.logIt_thread(self.log_path, msg=f'Updating connections list...')
                self.connections.update(self.temp_connection)
                self.logIt_thread(self.log_path, msg=f'Connections list updated.')

                # Set Temp Idents Dict For Idents
                self.logIt_thread(self.log_path, msg=f'Creating dict to hold ident details...')
                self.temp_ident = {self.conn: {self.ip: {self.ident: {self.user: self.client_version}}}}
                self.logIt_thread(self.log_path, msg=f'Dict created: {self.temp_ident}')

                # Add Temp Idents Dict To Idents Dict
                self.logIt_thread(self.log_path, msg=f'Updating live clients list...')
                self.clients.update(self.temp_ident)
                self.logIt_thread(self.log_path, msg=f'Live clients list updated.')

            # Create a Dict of Connection, IP, Computer Name, Date & Time
            self.logIt_thread(self.log_path, msg=f'Fetching current date & time...')
            dt = get_date()
            self.logIt_thread(self.log_path, msg=f'Creating a connection dict...')
            self.temp_connection_record = {self.conn: {self.ip: {self.ident: {self.user: dt}}}}
            self.logIt_thread(self.log_path, msg=f'Connection dict created: {self.temp_connection_record}')

            # Add Connection to Connection History
            self.logIt_thread(self.log_path, msg=f'Adding connection to connection history...')
            self.connHistory.append(self.temp_connection_record)
            self.logIt_thread(self.log_path, msg=f'Connection added to connection history.')

            self.logIt_thread(self.log_path, msg=f'Calling self.welcome_message() condition...')
            if self.welcome_message():
                continue

    def welcome_message(self) -> bool:
        self.logIt_thread(self.log_path, msg=f'Running welcome_message()...')

        # Send Welcome Message
        try:
            self.welcome = "Connection Established!"
            self.logIt_thread(self.log_path, msg=f'Sending welcome message...')
            self.conn.send(f"@Server: {self.welcome}".encode())
            self.logIt_thread(self.log_path, msg=f'{self.welcome} sent to {self.ident}.')

            return True

        except (WindowsError, socket.error) as e:
            self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
            if self.conn in self.targets and self.ip in self.ips:
                self.logIt_thread(self.log_path, msg=f'Removing {self.conn} from self.targets...')
                self.targets.remove(self.conn)

                self.logIt_thread(self.log_path, msg=f'Removing {self.ip} from self.ips list...')
                self.ips.remove(self.ip)

                self.logIt_thread(self.log_path, msg=f'Deleting {self.conn} from self.connections.')
                del self.connections[self.conn]

                self.logIt_thread(self.log_path, msg=f'Deleting {self.conn} from self.clients...')
                del self.clients[self.conn]

                self.logIt_thread(self.log_path, msg=f'[V]Connection removed from lists.')

                return False

    def connection_history(self) -> None:
        self.logIt_thread(self.log_path, msg=f'Running connection_history()...')
        c = 1  # Initiate Counter for Connection Number
        try:
            # Iterate Through Connection History List Items
            self.logIt_thread(self.log_path, msg=f'Iterating self.connHistory...')
            for connection in self.connHistory:
                for conKey, ipValue in connection.items():
                    for ipKey, identValue in ipValue.items():
                        for identKey, userValue in identValue.items():
                            for userKey, timeValue in userValue.items():
                                print(
                                    f"[{colored(str(c), 'green')}]{colored('IP', 'cyan')}: {ipKey} | "
                                    f"{colored('Station Name', 'cyan')}: {identKey} | "
                                    f"{colored('User', 'cyan')}: {userKey} | "
                                    f"{colored('Time', 'cyan')}: {str(timeValue).replace('|', ':')}")
                    c += 1

        # Break If Client Lost Connection
        except (KeyError, socket.error, ConnectionResetError) as e:
            self.logIt_thread(self.log_path, msg=f'Iteration Error: {e}')
            return

    def vital_signs(self) -> bool:
        self.logIt_thread(self.log_path, msg=f'Running vital_signs()...')

        self.logIt_thread(self.log_path,
                          msg=f'Init class: vitals({self.targets, self.ips, self.clients, self.connections, self.log_path})...')
        vitals = vital_signs.Vitals(self.targets, self.ips, self.clients,
                                    self.connections, self.log_path, self.ident)
        if vitals.vitals_input():
            vitals.vital_signs()
            return True

        else:
            self.logIt_thread(self.log_path, msg=f'Closing vital_signs()...')
            return False

    def show_available_connections(self) -> None:
        def make_tmp():
            count = 0
            for conKey, ipValue in self.clients.items():
                for ipKey, identValue in ipValue.items():
                    for con, ip in self.connections.items():
                        if ip == ipKey:
                            for identKey, userValue in identValue.items():
                                for userV, clientVer in userValue.items():
                                    if (count, ipKey, identKey, userValue) in self.tmp_availables:
                                        continue

                                self.tmp_availables.append((count, ipKey, identKey, userV, clientVer))
                count += 1

            self.logIt_thread(self.log_path, msg=f'Available list created.')

        def extract():
            for item in self.tmp_availables:
                for conKey, ipValue in self.clients.items():
                    for ipKey in ipValue.keys():
                        if item[1] == ipKey:
                            session = item[0]
                            stationIP = item[1]
                            stationName = item[2]
                            loggedUser = item[3]
                            clientVersion = item[4]
                            print(f"Session [{colored(f'{session}', 'cyan')}] | "
                                  f"Station IP: {colored(f'{stationIP}', 'green')} | "
                                  f"Station Name: {colored(f'{stationName}', 'green')} | "
                                  f"Logged User: {colored(f'{loggedUser}', 'green')} | "
                                  f"Client Version: {colored(clientVersion, 'green')}")

            print(f"\n[{colored('[Q/q]', 'cyan')}]Back")
            self.logIt_thread(self.log_path, msg=f'Extraction completed.')

        self.logIt_thread(self.log_path, msg=f'Running show_available_connections()...')
        if len(self.ips) == 0:
            self.logIt_thread(self.log_path, msg=f'No connected Stations')
            print(f"[{colored('*', 'cyan')}]No connected stations.\n")
            return

        # Cleaning availables list
        self.logIt_thread(self.log_path, msg=f'Cleaning availables list...')
        self.tmp_availables = []

        try:
            print(f"[{colored('*', 'cyan')}] {colored('Available Connections', 'green')} [{colored('*', 'cyan')}]")
            print(f"{colored('=', 'yellow') * 29}")

            self.logIt_thread(self.log_path, msg=f'Creating available list...')
            make_tmp()

            self.logIt_thread(self.log_path,
                              msg=f'Extracting: Session | Station IP | Station Name | Logged User '
                                  f'from clients list...')
            extract()

        except (WindowsError, socket.error) as e:
            self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
            print(f"[{colored('*', 'red')}]Connection terminated by the client.")

            self.logIt_thread(self.log_path, msg=f'Removing connection from available list...')
            self.remove_lost_connection(con, ip)
            self.logIt_thread(self.log_path, msg=f'Available list updated.')

            self.logIt_thread(self.log_path, msg=f'=== End of show_available_connections ===')

            return False

    def get_station_number(self) -> (int, int, int):
        self.logIt_thread(self.log_path, msg=f'Running get_station_number()...')
        if len(self.tmp_availables) == 0:
            self.logIt_thread(self.log_path, msg=f'No available connections.')
            print(f"[{colored('*', 'cyan')}]No available connections.\n")
            return

        tries = 1
        while True:
            self.logIt_thread(self.log_path, msg=f'Waiting for station number...')
            station_num = input(f"\n@Session #>> ")
            self.logIt_thread(self.log_path, msg=f'Station number: {station_num}')
            if str(station_num).lower() == 'q':
                self.logIt_thread(self.log_path, msg=f'Station number: {station_num} | moving back...')
                return False

            try:
                self.logIt_thread(self.log_path, msg=f'Running input validation on {station_num}')
                val = int(station_num)
                if int(station_num) <= 0 or int(station_num) <= (len(self.tmp_availables)):
                    tarnum = self.targets[int(station_num)]
                    ipnum = self.ips[int(station_num)]
                    self.logIt_thread(log_path, msg=f'=== End of get_station_number() ===')
                    return int(station_num), tarnum, ipnum

                else:
                    self.logIt_thread(log_path, msg=f'Wrong input detected.')
                    print(f"[{colored('*', 'red')}]Wrong Number. Choose between [1 - {len(self.tmp_availables)}].\n"
                          f"[Try {colored(f'{tries}', 'yellow')}/{colored('3', 'yellow')}]")

                    if tries == 3:
                        print("U obviously don't know what you're doing. goodbye.")
                        self.logIt_thread(self.log_path, msg=f'Tries: 3 | Ending program...')
                        if len(server.targets) > 0:
                            self.logIt_thread(self.log_path, msg=f'Closing live connections...')
                            for t in server.targets:
                                t.send('exit'.encode())
                                t.shutdown(socket.SHUT_RDWR)
                                t.close()

                            self.logIt_thread(self.log_path, msg=f'Live connections closed.')

                        self.logIt_thread(self.log_path, msg=f'Exiting app...')
                        sys.exit()

                    tries += 1

            except (TypeError, ValueError, IndexError):
                self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                print(f"[{colored('*', 'red')}]Numbers only. Choose between [1 - {len(self.tmp_availables)}].\n"
                      f"[Try {colored(f'{tries}', 'yellow')}/{colored('3', 'yellow')}]")
                if tries == 3:
                    dt = get_date()
                    if len(server.targets) > 0:
                        self.logIt_thread(self.log_path, msg=f'Closing live connections...')
                        for t in server.targets:
                            t.send('exit'.encode())
                            t.shutdown(socket.SHUT_RDWR)
                            t.close()

                        self.logIt_thread(self.log_path, msg=f'Live connections closed.')

                    print("U obviously don't know what you're doing. goodbye.")
                    self.logIt_thread(self.log_path, msg=f'Exiting app...')
                    sys.exit()

                tries += 1

    def show_shell_commands(self, ip: str) -> None:
        self.logIt_thread(self.log_path, msg=f'Running show_shell_commands()...')
        self.logIt_thread(self.log_path, msg=f'Displaying headline...')
        print("\t\t" + f"{colored('=', 'blue')}" * 20, f"=> {colored('REMOTE CONTROL', 'red')} <=",
              f"{colored('=', 'blue')}" * 20)

        self.logIt_thread(self.log_path, msg=f'Displaying Station IP | Station Name | Logged User in headline...')
        for conKey, ipValue in self.clients.items():
            for ipKey, userValue in ipValue.items():
                if ipKey == ip:
                    for item in self.tmp_availables:
                        if item[1] == ip:
                            for identKey, timeValue in userValue.items():
                                loggedUser = item[3]
                                clientVersion = item[4]
                                print("\t" + f"IP: {colored(f'{ipKey}', 'green')} | "
                                             f"Station Name: {colored(f'{identKey}', 'green')} | "
                                             f"Logged User: {colored(f'{loggedUser}', 'green')} | "
                                             f"Client Version: {colored(clientVersion, 'green')}")

        print("\t\t" + f"{colored('=', 'yellow')}" * 62 + "\n")

        self.logIt_thread(self.log_path, msg=f'Displaying shell commands menu...')
        print(f"\t\t[{colored('1', 'cyan')}]Screenshot          \t\t---------------> "
              f"Capture screenshot.")
        print(f"\t\t[{colored('2', 'cyan')}]System Info         \t\t---------------> "
              f"Show Station's System Information")
        print(f"\t\t[{colored('3', 'cyan')}]Last Restart Time   \t\t---------------> "
              f"Show remote station's last restart time")
        print(f"\t\t[{colored('4', 'cyan')}]Anydesk             \t\t---------------> "
              f"Start Anydesk")
        print(f"\t\t[{colored('5', 'cyan')}]Tasks               \t\t---------------> "
              f"Show remote station's running tasks")
        print(f"\t\t[{colored('6', 'cyan')}]Restart             \t\t---------------> "
              f"Restart remote station")
        print(f"\t\t[{colored('7', 'cyan')}]CLS                 \t\t---------------> "
              f"Clear Screen")
        print(f"\n\t\t[{colored('8', 'red')}]Back                \t\t---------------> "
              f"Back to Control Center \n")

        self.logIt_thread(self.log_path, msg=f'=== End of show_shell_commands() ===')

    def restart(self, con: str, ip: str) -> bool:
        def confirm_restart(con) -> bool:
            self.logIt_thread(self.log_path, msg=f'Running confirm_restart()...')
            tries = 0
            while True:
                try:
                    self.logIt_thread(self.log_path, msg=f'Running input validation on {self.sure}...')
                    str(self.sure)

                except TypeError:
                    self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                    print(f"[{colored('*', 'red')}]Wrong Input. [({colored('Y/y', 'yellow')}) | "
                          f"({colored('N/n', 'yellow')})]")

                    if tries == 3:
                        self.logIt_thread(self.log_path, msg=f'Tries: 3')
                        print("U obviously don't know what you're doing. goodbye.")
                        if len(server.targets) > 0:
                            self.logIt_thread(self.log_path, msg=f'Closing live connections...')
                            for t in server.targets:
                                t.send('exit'.encode())
                                t.shutdown(socket.SHUT_RDWR)
                                t.close()

                            self.logIt_thread(self.log_path, msg=f'Live connections closed.')

                        self.logIt_thread(self.log_path, msg=f'Exiting app with code 1...')
                        sys.exit(1)

                    tries += 1

                if str(self.sure).lower() == "y":
                    self.logIt_thread(self.log_path, msg=f'User input: {self.sure} | Returning TRUE...')
                    return True

                elif str(self.sure).lower() == "n":
                    self.logIt_thread(self.log_path, msg=f'User input: {self.sure} | Returning FALSE...')
                    con.send('n'.encode())
                    break

                else:
                    self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                    print(f"[{colored('*', 'red')}]Wrong Input. [({colored('Y/y', 'yellow')}) | "
                          f"({colored('N/n', 'yellow')})]")

                    if tries == 3:
                        self.logIt_thread(self.log_path, msg=f'Tries: 3')
                        print("U obviously don't know what you're doing. goodbye.")
                        if len(server.targets) > 0:
                            self.logIt_thread(self.log_path, msg=f'Closing live connections...')
                            dt = get_date()
                            for t in server.targets:
                                t.send('exit'.encode())
                                t.shutdown(socket.SHUT_RDWR)
                                t.close()

                            self.logIt_thread(self.log_path, msg=f'Live connections closed.')

                        self.logIt_thread(self.log_path, msg=f'Exiting app with code 1...')
                        sys.exit(1)

                    tries += 1

        self.logIt_thread(self.log_path, msg=f'Running restart({con}, {ip})...')
        errCount = 3
        self.sure = input("Are you sure you want to restart [Y/n]?")
        if confirm_restart(con):
            try:
                self.logIt_thread(self.log_path, msg=f'Sending restart command to client...')
                con.send('restart'.encode())
                try:
                    self.logIt_thread(self.log_path, msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                    self.remove_lost_connection(con, ip)
                    return True

                except RuntimeError as e:
                    self.logIt_thread(self.log_path, msg=f'Runtime Error: {e}')
                    return False

            except (WindowsError, socket.error) as e:
                self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
                print(f"[{colored('!', 'red')}]Client lost connection.")

                self.logIt_thread(self.log_path, msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                self.remove_lost_connection(con, ip)
                return False

        else:
            return False

    def anydesk(self, con: str, ip: str) -> bool:
        self.logIt_thread(self.log_path, msg=f'Running anydesk({con}, {ip})...')
        try:
            self.logIt_thread(self.log_path, msg=f'Sending anydesk command to {con}...')
            con.send('anydesk'.encode())
            self.logIt_thread(self.log_path, msg=f'Send Completed.')

            self.logIt_thread(self.log_path, msg=f'Waiting for response from client...')
            msg = con.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'Client response: {msg}.')

            if "OK" not in msg:
                self.logIt_thread(self.log_path, msg=f'Printing msg from client...')
                print(msg)
                while True:
                    try:
                        install_input = str(input("Install Anydesk [Y/n]? "))

                    except ValueError:
                        print(f"[{colored('!', 'red')}]Wrong input.")
                        continue

                    if str(install_input).lower() == "y":
                        print("Installing anydesk...")
                        self.logIt_thread(self.log_path, msg=f'Sending install command to {con}...')
                        con.send('y'.encode())
                        self.logIt_thread(self.log_path, msg=f'Send Completed.')

                        while True:
                            self.logIt_thread(self.log_path, msg=f'Waiting for response from client...')
                            msg = con.recv(1024).decode()
                            self.logIt_thread(self.log_path, msg=f'Client response: {msg}.')

                            if "OK" not in str(msg):
                                print(msg)
                                continue

                            else:
                                print(msg)
                                return False

                        return True

                    elif str(install_input).lower() == "n":
                        self.logIt_thread(self.log_path, msg=f'Sending cancel command to {con}...')
                        con.send('n'.encode())
                        self.logIt_thread(self.log_path, msg=f'Send Completed.')
                        break

                    else:
                        continue

        except (WindowsError, ConnectionError, socket.error) as e:
            self.logIt_thread(self.log_path, msg=f'Connection Error: {e}.')
            print(f"[{colored('!', 'red')}]Client lost connection.")
            try:
                self.logIt_thread(self.log_path, debug=True,
                                  msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                self.remove_lost_connection(con, ip)
                return False

            except RuntimeError as e:
                self.logIt_thread(self.log_path, debug=True, msg=f'Runtime Error: {e}.')
                return False

    def shell(self, con: str, ip: str) -> None:
        self.logIt_thread(self.log_path, msg=f'Running shell({con}, {ip})...')
        errCount = 0
        while True:
            self.logIt_thread(self.log_path, msg=f'Calling self.show_shell_commands({ip})...')
            self.show_shell_commands(ip)

            # Wait for User Input
            self.logIt_thread(self.log_path, msg=f'Waiting for user input...')
            cmd = input(f"COMMAND@{ip}> ")

            # Input Validation
            try:
                self.logIt_thread(self.log_path, msg=f'Performing input validation on user input: {cmd}...')
                val = int(cmd)

            except (TypeError, ValueError):
                self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                print(f"[{colored('*', 'red')}]Numbers Only [{colored('1', 'yellow')} - {colored('8', 'yellow')}]!")
                errCount += 1
                if errCount == 3:
                    self.logIt_thread(self.log_path, msg=f'Tries: 3')
                    print("U obviously don't know what you're doing. goodbye.")

                    self.logIt_thread(self.log_path, msg=f'Sending exit command to {ip}...')
                    con.send("exit".encode())
                    self.logIt_thread(self.log_path, msg=f'Send Completed.')

                    self.logIt_thread(self.log_path, msg=f'Closing connections...')
                    con.shutdown(socket.SHUT_RDWR)
                    con.close()
                    self.logIt_thread(self.log_path, msg=f'Connections closed.')

                    self.logIt_thread(self.log_path, msg=f'Exiting app with code 1...')
                    sys.exit(1)

                continue

            # Run Custom Command
            if int(cmd) == 100:
                self.logIt_thread(self.log_path, msg=f'Command: 100')
                try:
                    self.logIt_thread(self.log_path, msg=f'Send freestyle command...')
                    con.send("freestyle".encode())
                    self.logIt_thread(self.log_path, msg=f'Send Completed.')

                except (WindowsError, socket.error) as e:
                    self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
                    break

                for item, connection in zip(self.tmp_availables, self.connections):
                    for conKey, ipValue in self.clients.items():
                        if conKey == connection:
                            for ipKey in ipValue.keys():
                                if item[1] == ipKey:
                                    ipval = item[1]
                                    host = item[2]
                                    user = item[3]

                self.logIt_thread(self.log_path, msg=f'Initializing Freestyle Module...')
                free = freestyle.Freestyle(con, path, self.tmp_availables, self.clients,
                                           log_path, host, user)

                self.logIt_thread(self.log_path, msg=f'Calling freestyle module...')
                free.freestyle(ip)

                continue

            # Create INT Zone Condition
            self.logIt_thread(self.log_path, msg=f'Creating user input zone from 1-8...')
            if int(cmd) <= 0 or int(cmd) > 8:
                errCount += 1
                if errCount == 3:
                    self.logIt_thread(self.log_path, msg=f'Tries: 3')
                    print("U obviously don't know what you're doing. goodbye.")

                    self.logIt_thread(self.log_path, msg=f'Sending exit command to {ip}...')
                    con.send("exit".encode())
                    self.logIt_thread(self.log_path, msg=f'Send Completed.')

                    self.logIt_thread(self.log_path, msg=f'Closing connections...')
                    con.close()
                    self.logIt_thread(self.log_path, msg=f'Connections closed.')

                    self.logIt_thread(self.log_path, msg=f'Exiting app with code 1...')
                    sys.exit(1)

                self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                print(f"[{colored('*', 'red')}]{cmd} not in the menu."
                      f"[try {colored(errCount, 'yellow')} of {colored('3', 'yellow')}]\n")

            # Screenshot
            if int(cmd) == 1:
                self.logIt_thread(self.log_path, msg=f'Running screenshot condition...')
                errCount = 0
                if len(self.targets) == 0:
                    self.logIt_thread(self.log_path, msg=f'No available connections.')
                    print(f"[{colored('*', 'red')}]No connected stations.")
                    break

                try:
                    print(f"[{colored('*', 'cyan')}]Fetching screenshot...")
                    self.logIt_thread(self.log_path, msg=f'Sending screen command to client...')
                    con.send('screen'.encode())
                    self.logIt_thread(self.log_path, msg=f'Send Completed.')

                    self.logIt_thread(self.log_path, msg=f'Calling Module: '
                                                         f'screenshot({con, path, self.tmp_availables, self.clients})...')
                    scrnshot = screenshot.Screenshot(con, path, self.tmp_availables,
                                                     self.clients, self.log_path, self.targets)

                    self.logIt_thread(self.log_path, msg=f'Calling screenshot.recv_file()...')
                    scrnshot.recv_file(ip)

                except (WindowsError, socket.error, ConnectionResetError) as e:
                    self.logIt_thread(self.log_path, msg=f'Connection Error: {e}')
                    print(f"[{colored('!', 'red')}]Client lost connection.")

                    self.logIt_thread(self.log_path, msg=f'Calling self.remove_lost_connection({con}, {ip}...)')
                    self.remove_lost_connection(con, ip)
                    break

            # System Information
            elif int(cmd) == 2:
                self.logIt_thread(self.log_path, msg=f'Running system information condition...')
                errCount = 0
                if len(self.targets) == 0:
                    self.logIt_thread(self.log_path, msg=f'No available connections.')
                    print(f"[{colored('*', 'red')}]No connected stations.")
                    break

                try:
                    self.logIt_thread(self.log_path, msg=f'Initializing Module: sysinfo...')
                    sinfo = sysinfo.Sysinfo(con, self.ttl, path, self.tmp_availables, self.clients, self.log_path)

                    print(f"[{colored('*', 'cyan')}]Fetching system information, please wait... ")
                    self.logIt_thread(self.log_path, msg=f'Calling sysinfo.run()...')
                    if sinfo.run(ip):
                        print(f"[{colored('V', 'green')}]OK!")

                except (WindowsError, socket.error, ConnectionResetError) as e:
                    self.logIt_thread(self.log_path, debug=True, msg=f'Connection Error: {e}.')
                    # print(f"[{colored('!', 'red')}]Client lost connection.")
                    try:
                        self.logIt_thread(self.log_path, msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                        self.remove_lost_connection(con, ip)
                        return

                    except RuntimeError:
                        return

            # Last Restart Time
            elif int(cmd) == 3:
                self.logIt_thread(self.log_path, debug=False, msg=f'Running last restart condition...')
                errCount = 0
                if len(self.targets) == 0:
                    self.logIt_thread(self.log_path, debug=False, msg=f'No available connections.')
                    print(f"[{colored('*', 'red')}]No connected stations.")
                    break

                try:
                    self.logIt_thread(self.log_path, debug=False, msg=f'Sending lr command to client...')
                    con.send('lr'.encode())
                    self.logIt_thread(self.log_path, debug=False, msg=f'Send Completed.')

                    self.logIt_thread(self.log_path, debug=False, msg=f'Waiting for response from client...')
                    msg = con.recv(4096).decode()
                    self.logIt_thread(self.log_path, debug=False, msg=f'Client response: {msg}')
                    print(f"[{colored('@', 'green')}]{msg}")

                except (WindowsError, socket.error, ConnectionResetError) as e:
                    self.logIt_thread(self.log_path, debug=False, msg=f'Connection Error: {e}.')
                    print(f"[{colored('!', 'red')}]Client lost connection.")
                    try:
                        self.logIt_thread(self.log_path, debug=False,
                                          msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                        self.remove_lost_connection(con, ip)
                        break

                    except RuntimeError as e:
                        self.logIt_thread(self.log_path, debug=True, msg=f'Runtime Error: {e}.')
                        return

            # Anydesk
            elif int(cmd) == 4:
                self.logIt_thread(self.log_path, msg=f'Running anydesk condition...')
                errCount = 0
                print(f"[{colored('*', 'magenta')}]Starting AnyDesk...\n")
                self.logIt_thread(self.log_path, msg=f'Calling self.anydesk({con}, {ip})...')
                self.anydesk(con, ip)

            # Tasks
            elif int(cmd) == 5:
                self.logIt_thread(self.log_path, debug=False, msg=f'Running tasks condition...')
                errCount = 0
                if len(self.targets) == 0:
                    self.logIt_thread(self.log_path, debug=False, msg=f'No available connections.')
                    print(f"[{colored('*', 'red')}]No connected stations.")
                    break

                self.logIt_thread(self.log_path, debug=False, msg=f'Initializing Module: tasks...')
                tsks = tasks.Tasks(con, ip, ttl, self.clients, self.connections,
                                   self.targets, self.ips, self.tmp_availables, path, self.log_path)

                self.logIt_thread(self.log_path, debug=False, msg=f'Calling tasks.tasks()...')
                if not tsks.tasks(ip):
                    return False

                self.logIt_thread(self.log_path, debug=False, msg=f'Calling tasks.kill_tasks()...')
                task = tsks.kill_tasks(ip)
                if task is None:
                    continue

                try:
                    self.logIt_thread(self.log_path, debug=False, msg=f'Calling tasks.task_to_kill()...')
                    tasks.task_to_kill(ip)
                    return True

                except (WindowsError, socket.error, ConnectionResetError, ConnectionError) as e:
                    self.logIt_thread(self.log_path, debug=False, msg=f'Connection Error: {e}')
                    print(f"[{colored('!', 'red')}]Client lost connection.")
                    try:
                        self.logIt_thread(self.log_path, debug=False,
                                          msg=f'Calling self.remove_lost_connection({con}, {ip})...')
                        self.remove_lost_connection(con, ip)

                    except RuntimeError as e:
                        self.logIt_thread(self.log_path, debug=False, msg=f'Runtime Error: {e}.')
                        return False

            # Restart
            elif int(cmd) == 6:
                self.logIt_thread(self.log_path, debug=False, msg=f'Running restart condition...')
                self.logIt_thread(self.log_path, debug=False, msg=f'Calling self.restart({con}, {ip})...')
                if self.restart(con, ip):
                    break

            # Clear Screen
            elif int(cmd) == 7:
                self.logIt_thread(self.log_path, debug=False, msg=f'Running clear screen condition...')
                self.logIt_thread(self.log_path, debug=False, msg=f'Clearing screen...')
                os.system('cls')
                self.logIt_thread(self.log_path, debug=False, msg=f'Screen cleared.')
                continue

            # Back
            elif int(cmd) == 8:
                self.logIt_thread(self.log_path, debug=False, msg=f'Running back condition...')
                self.logIt_thread(self.log_path, debug=False, msg=f'Breaking shell loop...')
                break

        self.logIt_thread(self.log_path, debug=False, msg=f'=== End of shell() ===')

    def remove_lost_connection(self, con: str, ip: str) -> bool:
        self.logIt_thread(self.log_path, msg=f'Running remove_lost_connection({con}, {ip})...')
        try:
            self.logIt_thread(self.log_path, msg=f'Removing connections...')
            for conKey, ipValue in self.clients.items():
                if conKey == con:
                    for ipKey, identValue in ipValue.items():
                        if ipKey == ip:
                            for identKey, userValue in identValue.items():
                                self.targets.remove(con)
                                self.ips.remove(ip)

                                del self.connections[con]
                                del self.clients[con]
                                print(f"[{colored('*', 'red')}]{colored(f'{ip}', 'yellow')} | "
                                      f"{colored(f'{identKey}', 'yellow')} | "
                                      f"{colored(f'{userValue}', 'yellow')} "
                                      f"Removed from Availables list.\n")

            self.logIt_thread(self.log_path, msg=f'Connections removed.')
            return True

        except RuntimeError as e:
            self.logIt_thread(self.log_path, msg=f'Runtime Error: {e}.')
            return False


def get_date() -> str:
    d = datetime.now().replace(microsecond=0)
    dt = str(d.strftime("%b %d %Y | %I-%M-%S"))

    return dt


def get_random_string(length: int) -> str:
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)

    return result_str


if __name__ == "__main__":
    port = 55400
    ttl = 5
    hostname = socket.gethostname()
    serverIP = str(socket.gethostbyname(hostname))
    path = r'c:\Peach'
    log_path = fr'{path}\server_log.txt'

    engine = create_engine("sqlite:///peach.db", echo=True)
    Base.metadata.create_all(bind=engine)

    # while True:
    app.run(debug=True)
