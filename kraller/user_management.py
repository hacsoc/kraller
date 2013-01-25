from subprocess import PIPE, Popen, call

shells = {
   'bash': '/bin/bash',
   'zsh': '/bin/zsh',
   'tmux': '/usr/bin/tmux'
}

# TODO: Validate that GECOS can never have commas
# TODO: usernames should be [a-z0-9]

def create_user(username, full_name, room_number, work_phone, home_phone):
    gecos = ','.join([full_name, room_number, work_phone, home_phone])
    return call(['sudo', 'adduser', '--disabled-password', '--quiet', '--gecos', gecos, '--ingroup', 'users', username])

def add_ssh_key(username, ssh_key):
    #TODO validate ssh keys
    s = Popen(['sudo', '-H', '-u', username, '/usr/local/bin/add_ssh_key'], stdin=PIPE)
    s.stdin.write(ssh_key + "\n")
    s.stdin.close()
    return s.wait()
     

def change_gecos(username, gecos):
    return subprocess.call(['sudo', 'usermod', '-c', gecos, username])

def change_shell(username, shell):
    return subprocess.call(['sudo', 'usermod', '-s', shells[shell], username])
