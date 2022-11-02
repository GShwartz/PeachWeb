from datetime import datetime
from termcolor import colored
from threading import Thread
import socket
import shutil
import time
import os

# TODO: DONE: Logger
# TODO: DONE: Switched to real time streaming and save to local file


class Sysinfo:
    def __init__(self, con, ttl, root, tmp_availables, clients, log_path):
        self.con = con
        self.ttl = ttl
        self.root = root
        self.tmp_availables = tmp_availables
        self.clients = clients
        self.log_path = log_path

    def get_date(self):
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%b %d %Y %I.%M.%S %p"))

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

    def make_dir(self, ip: str) -> str:
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

    def run_command(self, ip, host, user):
        self.logIt_thread(self.log_path, msg=f'Running self.run_command()...')
        try:
            self.logIt_thread(self.log_path, msg=f'Sending si command to {self.con}...')
            self.con.send('si'.encode())
            self.logIt_thread(self.log_path, msg=f'Send complete.')

            self.logIt_thread(self.log_path, msg=f'Waiting for results from {self.con}...')
            result = self.con.recv(4096).decode()
            self.logIt_thread(self.log_path, msg=f'Results: {result}\n')
            print(result)

            self.logIt_thread(self.log_path, msg=f'Writing results to {self.sysinfo}...')
            if not os.path.exists(self.sysinfo):
                with open(self.sysinfo, 'w') as log:
                    log.write(f"====================================================\n")
                    log.write(f"IP: {ip} | NAME: {host} | LOGGED USED: {user}\n")
                    log.write(f"====================================================\n")
                    log.write(f"{result}\n\n")

            else:
                with open(self.sysinfo, 'a') as log:
                    log.write(f"====================================================")
                    log.write(f"IP: {ip} | NAME: {host} | LOGGED USED: {user}\n")
                    log.write(f"====================================================\n")
                    log.write(f"{result}\n\n")

            return True

        except (WindowsError, socket.error) as e:
            self.logIt_thread(self.log_path, msg=f'Connection error: {e}')
            return False

    def run(self, ip):
        dt = self.get_date()

        self.logIt_thread(self.log_path, msg=f'Running recv_file()...')
        self.logIt_thread(self.log_path, msg=f'Calling make_dir()...')
        name, loggedUser, path = self.make_dir(ip)

        self.logIt_thread(self.log_path, msg=f'Creating sysinfo file...')
        self.sysinfo = rf'C:\Peach\{name}\sysinfo {dt}.txt'

        self.logIt_thread(self.log_path, msg=f'Calling self.run_command()...')

        if self.run_command(ip, name, loggedUser):
            return True

        else:
            return False
