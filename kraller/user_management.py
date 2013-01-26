from pwd import getpwnam
from subprocess import PIPE, Popen, call

shells = {
    'bash': '/bin/bash',
    'zsh': '/bin/zsh',
    'tmux': '/usr/bin/tmux'
}


def try_getpwnam(name):
    try:
        return getpwnam(name)
    except KeyError:
        return None


def create_user(username, full_name, room_number, work_phone, home_phone):
    gecos = ','.join([full_name, room_number, work_phone, home_phone])
    return call(['sudo', '-n', '/usr/local/sbin/kraller_adduser', gecos, username])


def add_ssh_key(username, ssh_key):
    #TODO validate ssh keys
    s = Popen(['sudo', '-n', '-H', '-u', username, '/usr/local/bin/add_ssh_key'], stdin=PIPE)
    s.stdin.write(ssh_key + "\n")
    s.stdin.close()
    return s.wait()


def change_gecos(username, gecos):
    return subprocess.call(['sudo', '-n', 'usermod', '-c', gecos, username])


def change_shell(username, shell):
    return subprocess.call(['sudo', '-n', 'usermod', '-s', shells[shell], username])
