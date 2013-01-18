
shells = {
   'bash': '/bin/bash',
   'zsh': '/bin/zsh',
   'tmux': '/usr/bin/tmux'
}

# TODO: Validate that GECOS can never have commas

def create_user(username, full_name, room_number, work_phone, home_phone, ssh_key): 
    gecos = ','.join([full_name, room_number, work_phone, home_phone])
    subprocess.call(['sudo', 'adduser', '--disabled-password', '--quiet', '--gecos', gecos, '--ingroup', 'users', username])
    add_ssh_key(username, ssh_key)

def add_ssh_key(username, ssh_key):
    ssh_key_file = StringIO.StringIO(ssh_key)
    return subprocess.call(['sudo', '-H', '-u', username, '/usr/local/bin/add_ssh_key'], stdin=ssh_key_file)

def change_gecos(username, gecos):
    return subprocess.call(['sudo', 'usermod', '-c', gecos, username])

def change_shell(username, shell):
    return subprocess.call(['sudo', 'usermod', '-s', shells[shell], username)
