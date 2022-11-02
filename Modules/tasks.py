from datetime import datetime
from termcolor import colored
from threading import Thread
import ntpath
import socket
import shutil
import time
import os


class Tasks:
    def __init__(self, con, ip, ttl, clients, connections, targets, ips, tmp_availables, root, log_path):
        self.con = con
        self.ip = ip
        self.ttl = ttl
        self.clients = clients
        self.connections = connections
        self.targets = targets
        self.ips = ips
        self.tmp_availables = tmp_availables
        self.root = root
        self.log_path = log_path

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

    def tasks(self, ip):
        self.logIt_thread(self.log_path, msg=f'Running tasks({ip})...')
        print(f"[{colored('*', 'cyan')}]Retrieving remote station's task list\n"
              f"[{colored('*', 'cyan')}]Please wait...")
        try:
            self.logIt_thread(self.log_path, msg=f'Sending tasks command to {ip}...')
            self.con.send('tasks'.encode())
            self.logIt_thread(self.log_path, msg=f'Send complete.')

            self.logIt_thread(self.log_path, msg=f'Waiting for filename from {ip}...')
            filenameRecv = self.con.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'Filename: {filenameRecv}.')

            self.logIt_thread(self.log_path, msg=f'Sleeping for {self.ttl} seconds...')
            time.sleep(self.ttl)

            self.logIt_thread(self.log_path, msg=f'Waiting for file size from {ip}...')
            size = self.con.recv(4)
            self.logIt_thread(self.log_path, msg=f'Size: {size}.')

            self.logIt_thread(self.log_path, msg=f'Converting size bytes to numbers...')
            size = self.bytes_to_number(size)
            current_size = 0
            buffer = b""

            self.logIt_thread(self.log_path, msg=f'Renaming {filenameRecv}...')
            filenameRecv = str(filenameRecv).strip("b'")

            self.logIt_thread(self.log_path, msg=f'Calling self.make_dir({ip})...')
            name, loggedUser, path = self.make_dir(ip)

            self.logIt_thread(self.log_path, msg=f'Writing content to {filenameRecv}...')
            with open(filenameRecv, 'wb') as tsk_file:
                while current_size < size:
                    self.logIt_thread(self.log_path, msg=f'Receiving file content from {ip}...')
                    data = self.con.recv(1024)
                    if not data:
                        break

                    if len(data) + current_size > size:
                        data = data[:size - current_size]

                    buffer += data
                    current_size += len(data)
                    tsk_file.write(data)

            self.logIt_thread(self.log_path, msg=f'Printing file content to screen...')
            with open(filenameRecv, 'r') as file:
                data = file.read()
                print(data)

            self.logIt_thread(self.log_path, msg=f'Renaming {filenameRecv} to send to {ip}...')
            name = ntpath.basename(str(filenameRecv))

            self.logIt_thread(self.log_path, msg=f'Sending confirmation to {ip}...')
            self.con.send(f"Received file: {name}\n".encode())
            self.logIt_thread(self.log_path, msg=f'Send complete.')

            self.logIt_thread(self.log_path, msg=f'Waiting for closer from {ip}...')
            msg = self.con.recv(1024).decode()
            self.logIt_thread(self.log_path, msg=f'{ip}: {msg}')
            # print(f"[{colored('@', 'green')}]{msg}")

            # Move screenshot file to directory
            src = os.path.abspath(filenameRecv)
            dst = fr"{path}"

            self.logIt_thread(self.log_path, msg=f'Moving {src} to {dst}...')
            shutil.move(src, dst)

            return True

        except (WindowsError, socket.error) as e:
            self.logIt_thread(self.log_path, msg=f'Error: {e}')
            print(f"[{colored('!', 'red')}]{e}")
            self.remove_lost_connection()

    def kill_tasks(self, ip):
        self.logIt_thread(self.log_path, msg=f'Running self.kill_tasks()...')
        while True:
            try:
                self.logIt_thread(self.log_path, msg=f'Waiting for user confirmation...')
                choose_task = input(f"[?]Kill a task [Y/n]? ")

            except ValueError:
                self.logIt_thread(self.log_path, msg=f'Value Error!')
                print(f"[{colored('*', 'red')}]Choose [Y] or [N].")

            if choose_task.lower() == 'y':
                self.logIt_thread(self.log_path, msg=f'Calling self.task_to_kill()...')
                self.task_to_kill(ip)
                break

            elif choose_task.lower() == 'n':
                try:
                    self.logIt_thread(self.log_path, msg=f'Sending pass command to {ip}...')
                    self.con.send('pass'.encode())
                    self.logIt_thread(self.log_path, msg=f'Send complete.')
                    break

                except Exception as e:
                    self.logIt_thread(self.log_path, msg=f'Error: {e}')
                    self.remove_lost_connection()
                    break

            else:
                self.logIt_thread(self.log_path, msg=f'Wrong input detected.')
                print(f"[{colored('*', 'red')}]Choose [Y] or [N].\n")

        return

    def task_to_kill(self, ip):
        self.logIt_thread(self.log_path, msg=f'Running self.task_to_kill()...')
        while True:
            self.logIt_thread(self.log_path, msg=f'Waiting for user input...')
            task_to_kill = input(f"Task filename [Q Back]: ")
            if str(task_to_kill).lower() == 'q':
                break

            if str(task_to_kill).endswith('exe'):
                if self.confirm_kill(task_to_kill).lower() == "y":
                    try:
                        self.logIt_thread(self.log_path, msg=f'Sending kill command to {ip}.')
                        self.con.send('kill'.encode())
                        self.logIt_thread(self.log_path, msg=f'Send complete.')

                        self.logIt_thread(self.log_path, msg=f'Sending task name to {ip}...')
                        self.con.send(task_to_kill.encode())
                        self.logIt_thread(self.log_path, msg=f'Send complete.')

                        self.logIt_thread(self.log_path, msg=f'Waiting for confirmation from {ip}...')
                        msg = self.con.recv(1024).decode()
                        self.logIt_thread(self.log_path, msg=f'{ip}: {msg}')
                        print(f"[{colored('*', 'green')}]{msg}\n")
                        break

                    except (WindowsError, socket.error) as e:
                        self.logIt_thread(self.log_path, msg=f'Error: {e}.')
                        print(f"[{colored('!', 'red')}]Client lost connection.")
                        self.remove_lost_connection()

                else:
                    self.logIt_thread(self.log_path, msg=f'Sending pass command to {ip}.')
                    self.con.send('pass'.encode())
                    self.logIt_thread(self.log_path, msg=f'Send complete.')
                    break

            else:
                self.logIt_thread(self.log_path, msg=f'Error: {task_to_kill} not found.')
                print(f"[{colored('*', 'red')}]{task_to_kill} not found.")

        self.logIt_thread(self.log_path, msg=f'Task to kill: {task_to_kill}.')
        return task_to_kill

    def confirm_kill(self, task_to_kill):
        self.logIt_thread(self.log_path, msg=f'Running self.confirm_kill({task_to_kill})...')
        while True:
            self.logIt_thread(self.log_path, msg=f'Waiting for user confirmation...')
            confirm_kill = input(f"Are you sure you want to kill {task_to_kill} [Y/n]? ")
            if confirm_kill.lower() == "y":
                break

            elif confirm_kill.lower() == "n":
                break

            else:
                print(f"[{colored('*', 'red')}]Choose [Y] or [N].")

        self.logIt_thread(self.log_path, msg=f'Confirmation: {confirm_kill}')
        return confirm_kill

    def remove_lost_connection(self):
        self.logIt_thread(self.log_path, msg=f'Running self.remove_lost_connection()...')
        try:
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
            return False

        except Exception as e:
            self.logIt_thread(self.log_path, msg=f'Error: {e}.')
            return False
