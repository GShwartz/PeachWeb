from termcolor import colored
from datetime import datetime
from threading import Thread
import socket
import time
import os

# TODO: DONE: Finished Logger + Recv client version


class Vitals:
    threads = []

    def __init__(self, targets, ips, clients, connections, log_path, ident):
        self.targets = targets
        self.ips = ips
        self.clients = clients
        self.connections = connections
        self.log_path = log_path
        self.ident = ident

        # Capture Current Connected Sockets
        self.tmpconns = self.targets

        # Create Temp Lists For Socket Connections and IPs
        self.templist = []
        self.tempips = []

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
        self.threads.append(self.logit_thread)
        return

    def remove_lost_connection(self, con, ip):
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

    def vitals_input(self):
        self.logIt_thread(self.log_path, msg=f'Running vitals_input()...')
        while True:
            self.logIt_thread(self.log_path, msg=f'Waiting for user input...')
            pick = input("CONTROL@> ")
            self.logIt_thread(self.log_path, msg=f'User input: {pick}.')

            self.logIt_thread(self.log_path, msg=f'Performing input validation on {pick}.')
            try:
                float(pick)

            except ValueError as e:
                self.logIt_thread(self.log_path, msg=f'Value Error: {e}.')
                print(f"[{colored('*', 'red')}]Value Error.")
                continue

            # Start
            if int(pick) == 1:
                self.logIt_thread(self.log_path, msg=f'Returning True...')
                return True

            # Back
            elif int(pick) == 2:
                self.logIt_thread(self.log_path, msg=f'Returning False...')
                return False

            else:
                self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                print(f"[{colored('*', 'red')}]Wrong Number! "
                      f"[{colored('1', 'yellow')} - {colored('3', 'yellow')}]")

    def vital_signs(self):
        if len(self.targets) == 0:
            self.logIt_thread(self.log_path, msg=f'No connected stations.')
            print(f"[{colored('*', 'yellow')}]No connected stations.")

            self.logIt_thread(self.log_path, msg=f'Returning False.')
            return False

        self.logIt_thread(self.log_path, msg=f'Setting callback to "yes" & i=0')
        callback = 'yes'
        i = 0

        self.logIt_thread(self.log_path, msg=f'Iterating Through Temp Connected Sockets List...')
        for t in self.tmpconns:
            try:
                self.logIt_thread(self.log_path, msg=f'Sending "alive" to {t}...')
                t.send('alive'.encode())
                self.logIt_thread(self.log_path, msg=f'Send completed.')

                self.logIt_thread(self.log_path, msg=f'Waiting for response from {t}...')
                ans = t.recv(1024).decode()
                self.logIt_thread(self.log_path, msg=f'Response from {t}: {ans}.')

                self.logIt_thread(self.log_path, msg=f'Waiting for client version from {t}...')
                ver = t.recv(1024).decode()
                self.logIt_thread(self.log_path, msg=f'Response from {t}: {ver}.')

                self.logIt_thread(self.log_path, msg=f'Comparing response to callback...')
                if str(ans) == str(callback):
                    try:
                        for conKey, ipValue in self.clients.items():
                            for ipKey, identValue in ipValue.items():
                                for con, ip in self.connections.items():
                                    if t == con:
                                        for name, version in identValue.items():
                                            for v, v1 in version.items():
                                                print(f"[{colored('V', 'green')}]{self.ips[i]} | {name} | Version: {v1}")
                                                self.logIt_thread(self.log_path, msg=f'Appending {self.targets[i]} to self.templist...')
                                                self.templist.append(self.targets[i])
                                                self.logIt_thread(self.log_path, msg=f'self.templist updated.')

                                                self.logIt_thread(self.log_path, msg=f'Appending {self.ips[i]} to self.ips...')
                                                self.tempips.append(self.ips[i])
                                                self.logIt_thread(self.log_path, msg=f'self.ips updated.')

                                                i += 1
                                                time.sleep(1)

                    except IndexError:
                        pass

            except ConnectionResetError as e:
                self.logIt_thread(self.log_path, msg=f'Connection Error: {e}.')
                print(f"[{colored('*', 'red')}]{self.ips[i]} does not respond.")
                self.remove_lost_connection(t, self.ips[i])

        # Reset Temp Lists
        self.logIt_thread(self.log_path, msg=f'Resetting {self.tmpconns} | {self.tempips} | {self.templist}...')
        self.tmpconns = []
        self.tempips = []
        self.templist = []
        self.logIt_thread(self.log_path, msg=f'{self.tmpconns} | {self.tempips} | {self.templist}...')

        self.logIt_thread(self.log_path, msg=f'=== End of vital_signs() ===')
        print(f"\n[{colored('*', 'green')}]Vital Signs Process completed.\n")

        return
