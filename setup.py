#!/usr/bin/env python3

import os, sys, shutil, fnmatch, subprocess, pwd
import argparse

DIR = os.path.abspath(os.path.dirname(__file__))

parser = argparse.ArgumentParser(description='An install script for epsilon.')
parser.add_argument('--prefix', default='/opt/epsilon', help='the prefix that epsilon should be installed under')
parser.add_argument('--noserver', default=False, action='store_true', help='don\'t install server')
parser.add_argument('--nojudge', default=False, action='store_true', help='don\'t install judge')
parser.add_argument('--nojail', default=False, action='store_true', help='don\'t build judge jail')
parser.add_argument('--nomanualjudge', default=False, action='store_true', help='don\'t install the manual judge')
parser.add_argument('action', help='"install" or "uninstall"')
opts = parser.parse_args()

opts.prefix = os.path.abspath(opts.prefix).rstrip('/')

BIN_PATH = '/usr/local/bin'

PERMS = [
    ('*', (644, 755, 'root')),
    ('./judge/execute-submission.sh', (755, 755, 'root')),
    ('./judge/jail-setup.sh', (744, 744, 'root')),
    ('./judge/jail-destroy.sh', (744, 744, 'root')),
    ('./judge/submissions', (777, 777, 'root')),
    ('./judge/scripts/*.sh', (755, 755, 'root')),
    ('./server/db/setup_db.sh', (755, 755, 'root')),
    ('./bin/epsilon-judge', (755, 755, 'root')),
    ('./bin/epsilon-server', (755, 755, 'root')),
    ('./bin/epsilon-manual-judge', (755, 755, 'root')),
    ('./bin/epsilon-manual-judge-start', (755, 755, 'root')),
]

KEYS = {
    'PREFIX': opts.prefix,
    'JUDGE_USER_PREFIX': 'epsilon',
    'JUDGE_USERS': '4'
}

KEY_EXPAND = [
    '*.sh',
    '*.py',
    # '*.html'
    './bin/epsilon-judge',
    './bin/epsilon-server',
    './bin/epsilon-manual-judge',
    '*.ini',
    '*.yml',
]

EXECUTABLES = {
    # Programming languages
    'JS': ['js', 'js24'],
    'PYTHON2': ['python2', 'python2.7'],
    'PYTHON3': ['python3', 'python3.3', 'python3.2'],
    'GPP': ['g++'],
    'GCC': ['gcc'],
    'RUBY': ['ruby'],
    'PERL': ['perl'],
    'JAVAC': ['javac'],
    'JAVA': ['java'],
    'DMCS': ['dmcs'],
    'MONO': ['mono'],
    'PASCAL': ['fpc'],
    'PASCAL_PPC': ['ppcx64', 'ppc386'],
    'OCTAVE': ['octave'],
    'OCTAVE_CLI': ['octave-cli'],

    # Other executables
    'SAFEEXEC': ['safeexec'],
    'BASH': ['bash'],
    'SH': ['sh'],
    'LOCALE': ['locale'],
    'LOCALE_GEN': ['locale-gen'],
    'LOCALEDEF': ['localedef'],
    'LDCONFIG': ['ldconfig'],
    'LDCONFIG_REAL': ['ldconfig.real'],
}

OPTIONAL_EXECUTABLES = {
    'OCTAVE_CLI',
    'PASCAL_PPC',
    'LDCONFIG_REAL',
}

PROG_LANGS = {
    ('js', 'JS'),
    ('python2', 'PYTHON2'),
    ('python3', 'PYTHON3'),
    ('ruby', 'RUBY'),
    ('perl', 'PERL'),
    ('java', 'JAVA'),
    ('mono', 'MONO'),
    ('octave', 'OCTAVE'),
}

def log(txt):
    sys.stdout.write("%s\n" % txt)

def fatal(error):
    sys.stderr.write('error: %s\n' % error)
    sys.exit(1)

def sh(cmd, cwd=None, die=True):
    global opts
    if cwd is None: cwd = opts.prefix
    sub = subprocess.Popen(cmd, cwd=cwd)
    if sub.wait() != 0 and die:
        fatal('command failed: %s' % ' '.join(cmd))

def sh_com(cmd, stdin, cwd=None, die=True):
    global opts
    if cwd is None: cwd = opts.prefix
    sub = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cwd)
    stdout, stderr = sub.communicate(stdin)
    if sub.returncode != 0 and die:
        fatal('command failed: %s' % ' '.join(cmd))
    return stdout.decode('utf-8')

def updateperms(path):
    global opts
    dest = os.path.join(opts.prefix, path)

    for glob, (f, d, u) in reversed(PERMS):
        if fnmatch.fnmatch(path, glob):
            if os.path.isfile(path):
                sh(['chmod', str(f), path])
            else:
                sh(['chmod', str(d), path])

            sh(['chown', u, path])
            break

def copy(path):
    global opts
    src = os.path.abspath(os.path.join(DIR, path))
    dest = os.path.abspath(os.path.join(opts.prefix, path))

    log('copying %s' % path)

    found = False
    for glob in KEY_EXPAND:
        if fnmatch.fnmatch(path, glob):
            found = True
            break

    if found:

        with open(src, 'r', encoding='utf-8') as f:
            txt = f.read()

        tat = 0
        res = ''
        while tat < len(txt):
            if txt[tat] == '_' and txt[tat+1] == '_':
                cnt = 0
                at = tat + 2
                while at + cnt + 1 < len(txt) and (ord('A') <= ord(txt[at + cnt]) <= ord('Z') or txt[at + cnt] == '_' or ord('0') <= ord(txt[at + cnt]) <= ord('9')):
                    if txt[at + cnt] == '_' and txt[at + cnt + 1] == '_':
                        break
                    cnt += 1

                pre = 'EPSILON_'
                if (at + cnt + 1 < len(txt)
                    and txt[at + cnt] == '_'
                    and txt[at + cnt + 1] == '_'
                    and txt[at:at+len(pre)] == pre):
                    if txt[at+len(pre):at+cnt] in KEYS:
                        res += KEYS[txt[at+len(pre):at+cnt]]
                        tat += cnt + 4
                    else:
                        fatal('key %s not found' % txt[at+len(pre):at+cnt])
                else:
                    res += txt[tat]
                    tat += 1
            else:
                res += txt[tat]
                tat += 1

        with open(dest, 'w', encoding='utf-8') as f:
            f.write(res)

    else:
        shutil.copyfile(src, dest)

def update(path):
    global opts
    src = os.path.abspath(os.path.join(DIR, path))
    dest = os.path.abspath(os.path.join(opts.prefix, path))
    log('updating %s' % dest)

    if os.path.isfile(dest):
        os.unlink(dest)

    if not os.path.exists(dest):
        os.mkdir(dest)

    updateperms(path)

    for f in os.listdir(src):

        if os.path.isdir(os.path.join(src, f)):

            update(os.path.join(path, f))

        else:

            if os.path.isdir(os.path.join(dest, f)):
                shutil.rmtree(os.path.join(dest, f))

            if os.path.isfile(os.path.join(dest, f)):
                os.unlink(os.path.join(dest, f))

            copy(os.path.join(path, f))

            updateperms(os.path.join(path, f))

def setup_virtualenv(path):
    global opts
    path = os.path.abspath(os.path.join(opts.prefix, path))
    if not os.path.exists(os.path.join(path, 'venv')):
        log('setting up virtualenv at %s' % path)
        sh(['virtualenv', '--no-site-packages', '-p', 'python3.3', 'venv'], cwd=path)

    log('updating virtualenv requirements at %s' % path)
    sh(['bash', '-c', '''
        source ./venv/bin/activate
        pip install -r requirements.txt
    '''], cwd=path)

def prepare():

    log('resolving executable paths')
    for key_name, exec_paths in EXECUTABLES.items():
        found = None
        for exec_path in exec_paths:
            if exec_path.startswith('/'):
                if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
                    found = exec_path
            else:
                found = shutil.which(exec_path)

            if found is not None:
                break

        if found is None:
            if key_name in OPTIONAL_EXECUTABLES:
                KEYS['EXE_' + key_name] = ''
                KEYS['LIBS_' + key_name] = ''
            else:
                fatal('no path found for executable %s' % key_name)
        else:
            KEYS['EXE_' + key_name] = found
            log('path for executable %s is %s' % (key_name, found))
            ldd = sh_com(['ldd', found], None, cwd='/', die=False)
            libs = []
            if ldd.strip() != 'not a dynamic executable':
                for line in ldd.strip().split('\n'):
                    sline = line.split('(')[0].strip()
                    if '=>' in sline:
                        rest = sline.split('=>')[1].strip()
                        if rest:
                            libs.append(rest)
                    else:
                        libs.append(sline)

            if libs:
                KEYS['LIBS_' + key_name] = ', ' + ', '.join(libs)
                log('libraries for %s are %s' % (key_name, ', '.join(libs)))
            else:
                KEYS['LIBS_' + key_name] = ''

        if key_name in OPTIONAL_EXECUTABLES:
            KEYS['OPT_EXE_' + key_name] = ', ' + found if found else ''

def install():
    global opts

    # TODO: make this optional if not installing judge
    log('installing safeexec')
    sh(['make'], cwd=os.path.join(DIR, 'judge/SafeExec'))
    sh(['make', 'install'], cwd=os.path.join(DIR, 'judge/SafeExec'))
    sh(['make', 'clean'], cwd=os.path.join(DIR, 'judge/SafeExec'))

    prepare()

    if not os.path.isdir(opts.prefix):
        os.makedirs(opts.prefix)

    log('installing necessary files')
    updateperms('.')

    log('config files')
    update('./config')

    log('files for the library')
    update('./lib')

    log('files for the virtualenv')
    copy('./requirements.txt')
    updateperms('./requirements.txt')
    setup_virtualenv('.')

    log('executables')
    update('./bin')

    if not opts.noserver:
        log('files for the server')
        update('./server')
        sh(['ln', '-sf', os.path.join(opts.prefix, 'bin/epsilon-server'), os.path.join(BIN_PATH, 'epsilon-server')])

    if not opts.nojudge:
        log('files for the judge')
        update('./judge')
        sh(['ln', '-sf', os.path.join(opts.prefix, 'bin/epsilon-judge'), os.path.join(BIN_PATH, 'epsilon-judge')])

        if not opts.nojail:
            log('destroying the jail, if it exists')
            sh(['./jail-destroy.sh'], cwd=os.path.join(opts.prefix, './judge'))
            log('creating the jail')
            sh(['./jail-setup.sh'], cwd=os.path.join(opts.prefix, './judge'))

            log('creating symlinks for programming languages')
            sh(['mkdir', os.path.join(opts.prefix, 'judge/jail/bin/lang/')])
            for lang, key_name in PROG_LANGS:
                sh(['ln', '-sf', KEYS['EXE_' + key_name], os.path.join(opts.prefix, 'judge/jail/bin/lang/' + lang)])

    if not opts.nomanualjudge:
        log('files for the manual judge')
        update('./manual_judge')
        sh(['ln', '-sf', os.path.join(opts.prefix, 'bin/epsilon-manual-judge'), os.path.join(BIN_PATH, 'epsilon-manual-judge')])

    log('')
    log('')
    log('Installation succeeded.')

    if not opts.nojudge:
        log('Please do the following:')
        log('')
        log('   - append the following to /etc/sudoers (where your_username is the user who will be running epsilon judge):')
        log('        your_username ALL=(root) NOPASSWD: %s/judge/execute-submission.sh' % opts.prefix)

    log('')
    log('')

def uninstall():
    global opts

    if os.path.exists(os.path.join(opts.prefix, 'judge/jail-destroy.sh')):
        log('destroying the jail')
        sh(['./jail-destroy.sh'], cwd=os.path.join(opts.prefix, 'judge'))

    log('removing binaries')
    os.unlink(os.path.join(BIN_PATH, 'epsilon-server'))
    os.unlink(os.path.join(BIN_PATH, 'epsilon-judge'))
    os.unlink(os.path.join(BIN_PATH, 'epsilon-manual-judge'))

    log('erasing the whole prefix directory')
    shutil.rmtree(opts.prefix, ignore_errors=True)

    log('uninstalling safeexec')
    sh(['make', 'uninstall'], cwd=os.path.join(DIR, 'judge/SafeExec'))

if opts.action == 'install':
    install()
elif opts.action == 'uninstall':
    uninstall()
else:
    sys.stderr.write('error: action must be either "install" or "uninstall"\n')
    parser.print_help()
    sys.exit(1)

