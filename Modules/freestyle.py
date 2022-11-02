import os
import time
import socket
import shutil
from termcolor import colored
from threading import Thread
from datetime import datetime


# TODO: FINISHED: logging.


class Freestyle:
    def __init__(self, con, root, tmp_availables, clients, logpath, host, user):
        self.host = host
        self.user = user
        self.con = con
        self.root = root
        self.tmp_availables = tmp_availables
        self.clients = clients
        self.log_path = logpath

    def get_date(self):
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%m/%d/%Y %H:%M:%S"))

        return dt

    def logIt(self, logfile=None, debug=None, msg=''):
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

    def logIt_thread(self, log_path=None, debug=False, msg=''):
        self.logit_thread = Thread(target=self.logIt, args=(log_path, debug, msg), name="Log Thread")
        self.logit_thread.start()
        return

    def bytes_to_number(self, b):
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def freestyle_menu(self):
        self.logIt_thread(self.log_path, debug=False, msg=f'Running freestyle_menu()...')
        print(f"\t\t({colored('1', 'yellow')})Run Powershell Command")
        print(f"\t\t({colored('2', 'yellow')})Run CMD Command")
        print(f"\n\t\t({colored('0', 'yellow')})Back")

        return

    def make_dir(self, ip):
        self.logIt_thread(self.log_path, msg=f'Running make_dir()...')
        self.logIt_thread(self.log_path, msg=f'Creating Directory...')

        for conKey, ipValue in self.clients.items():
            for ipKey, userValue in ipValue.items():
                if ipKey == ip:
                    for item in self.tmp_availables:
                        if item[1] == ip:
                            for identKey, timeValue in userValue.items():
                                name = item[2]
                                loggedUser = item[3]
                                clientVersion = item[4]
                                path = os.path.join(self.root, name)

                                try:
                                    os.makedirs(path)

                                except FileExistsError:
                                    self.logIt_thread(self.log_path, msg=f'Passing FileExistsError...')
                                    pass

        return name, loggedUser, path

    def freestyle(self, ip):
        name, loggedUser, path = self.make_dir(ip)
        self.cmd_log = rf'C:\Peach\{name}\cmd_log.txt'

        while True:
            try:
                self.logIt_thread(self.log_path, msg=f'Waiting for user input...')
                cmd = input(f"{ip}|{name}♦CMD>")
                self.logIt_thread(self.log_path, msg=f'User input: {cmd}')

                if str(cmd).lower()[:4] == "back":
                    self.logIt_thread(self.log_path, msg=f'Sending {cmd} command to client...')
                    self.con.send("back".encode())
                    self.logIt_thread(self.log_path, msg=f'Send completed.')
                    break

                self.logIt_thread(self.log_path, msg=f'Sending {cmd} to client...')
                self.con.send(cmd.encode())
                self.logIt_thread(self.log_path, msg=f'Send completed.')

                while True:
                    result = self.con.recv(1024).decode()

                    if "END" in str(result):
                        break

                    print(result)

                    if not os.path.exists(self.cmd_log):
                        with open(self.cmd_log, 'w') as log:
                            log.write(f"=-=-=-=-=-=-=-=-=-=-=-=| IP: {ip} | STATION: {name} | USER: {loggedUser} "
                                      f"|=-=-=-=-=-=-=-=-=-=-=-=\n")
                            log.write(f"Command: {cmd}\n")
                            log.write(f"{result}\n\n")

                    else:
                        with open(self.cmd_log, 'a') as log:
                            log.write(f"=-=-=-=-=-=-=-=-=-=-=-=| IP: {ip} | STATION: {name} | USER: {loggedUser} "
                                      f"|=-=-=-=-=-=-=-=-=-=-=-=\n")
                            log.write(f"Command: {cmd}\n")
                            log.write(f"{result}\n\n")

            except (WindowsError, socket.error) as e:
                self.logIt_thread(self.log_path, debug=True, msg=f'Error: {e}')
                return False
