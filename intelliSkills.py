'''
Insert GitHub repo ids, get their languages.
Insert GitHub user ids, get their languages.
Experimental, small input recommended.
Description is self explanatory.

@since 1.0
@author Oskar Jarczyk

@update 6.01.2014
'''

version_name = 'version 1.0 codename: perun'

from intelliRepository import MyRepository
from github import Github, UnknownObjectException, GithubException
import csv
import getopt
import scream
import gc
import sys
import codecs
import cStringIO
import __builtin__
import time
import datetime

auth_with_tokens = False
use_utf8 = True
resume_on_repo = None
resume_stage = None
resume_entity = None
quota_check = 0


def usage():
    f = open('usage.txt', 'r')
    for line in f:
        print line


try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:u:r:s:v", ["help", "tokens=",
                               "utf8=", "resume=", "resumestage=", "verbose"])
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-v", "--verbose"):
        __builtin__.verbose = True
        scream.ssay('Enabling verbose mode.')
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-t", "--tokens"):
        auth_with_tokens = (a in ['true', 'True'])
    elif o in ("-u", "--utf8"):
        use_utf8 = (a not in ['false', 'False'])
    elif o in ("-r", "--resume"):
        resume_on_repo = a
        scream.ssay('Resume on repo? ' + str(resume_on_repo))
    elif o in ("-s", "--resumestage"):
        resume_stage = a
        scream.ssay('Resume on repository with name ' + str(resume_stage))

repos = dict()

repos_filename = 'repos.txt'
repos_csv_filename = 'repos.csv'
users_filename = 'users.txt'
users_csv_filename = 'users.csv'
repos_reported_nonexist = []


class MyDialect(csv.Dialect):
    strict = True
    skipinitialspace = True
    quoting = csv.QUOTE_MINIMAL
    delimiter = ','
    escapechar = '\\'
    quotechar = '"'
    lineterminator = '\n'


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=MyDialect, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def make_headers():
    'If we are resuming program then dont create headers - '
    'CSV files are already created and they have some data'
    if resume_on_repo is None:
        with open(repos_csv_filename, 'ab') as output_csvfile:
            repowriter = UnicodeWriter(output_csvfile) if use_utf8 else csv.writer(output_csvfile, dialect=MyDialect)
            tempv = ('name', 'owner', 'lang1', 'lang2', 'lang3')
            repowriter.writerow(tempv)

        with open(users_csv_filename, 'ab') as output_csvfile:
            ccomentswriter = UnicodeWriter(output_csvfile) if use_utf8 else csv.writer(output_csvfile, dialect=MyDialect)
            tempv = ('repo_name', 'repo_owner', 'lang1', 'lang2', 'lang3')
            ccomentswriter.writerow(tempv)


def check_quota_limit():
    global quota_check
    quota_check += 1
    if quota_check > 9:
        quota_check = 0
        limit = gh.get_rate_limit()
        scream.ssay('Rate limit: ' + str(limit.rate.limit) +
                    ' remaining: ' + str(limit.rate.remaining))
        reset_time = gh.rate_limiting_resettime
        scream.ssay('Rate limit reset time: ' + str(reset_time))

        if limit.rate.remaining < 10:
            freeze()


def freeze():
    sleepy_head_time = 60 * 60
    time.sleep(sleepy_head_time)
    limit = gh.get_rate_limit()
    while limit.rate.remaining < 15:
        time.sleep(sleepy_head_time)


def freeze_more():
    freeze()


if __name__ == "__main__":
    scream.say('Start main execution')
    scream.say(version_name)

    secrets = []
    credential_list = []
    with open('pass.txt', 'r') as passfile:
        line__id = 0
        for line in passfile:
            line__id += 1
            secrets.append(line)
            if line__id % 4 == 0:
                login_or_token__ = str(secrets[0]).strip()
                pass_string = str(secrets[1]).strip()
                client_id__ = str(secrets[2]).strip()
                client_secret__ = str(secrets[3]).strip()
                credential_list.append({'login' : login_or_token__ , 'pass' : pass_string , 'client_id' : client_id__ , 'client_secret' : client_secret__})
                del secrets[:]

    scream.say(str(len(credential_list)) + ' full credentials successfully loaded')

    if auth_with_tokens:
        gh = Github(client_id=credential_list[0]['client_id'], client_secret=credential_list[0]['client_secret'])
        print credential_list[0]['client_id']
        print credential_list[0]['client_secret']
        print gh.oauth_scopes
        print gh.rate_limiting
    else:
        #print login_or_token__
        #print pass_string
        gh = Github(credential_list[0]['login'], credential_list[0]['pass'])

    is_gc_turned_on = 'turned on' if str(gc.isenabled()) else 'turned off'
    scream.ssay('Garbage collector is ' + is_gc_turned_on)

    make_headers()

    with open(repos_filename, 'rb') as source_csvfile:
        reposReader = csv.reader(source_csvfile, delimiter=',')
        for row in reposReader:
            key = str(row[0])
            print 'Adding ' + key + ' to list.'

            repo = MyRepository()
            repo.setKey(key)
            owner = key.split('/')[0]
            name = key.split('/')[1]
            repo.setInitials(name, owner)

            #check here if repo dont exist already in dictionary!
            if key in repos:
                scream.log('We already found rep ' + key +
                           ' in the dictionary..')
            else:
                repos[key] = repo


    iteration_step_count = 0

    with open(repos_csv_filename, 'wb') as csvfilerlw:
        rlw = csv.writer(csvfilerlw, delimiter=',',
                         quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for key in repos:

            if resume_on_repo is not None:
                resume_on_repo_name = resume_on_repo.split(',')[0]
                resume_on_repo_owner = resume_on_repo.split(',')[1]

                if not ((resume_on_repo_name == repo.getName()) and
                        (resume_on_repo_owner == repo.getOwner())):
                    iteration_step_count += 1
                    continue

            try:
                repository_object = repos[key]
                repository = gh.get_repo(key)
                repo.setRepoObject(repository)
            except UnknownObjectException as e:
                scream.log_warning('Repo with key + ' + key +
                                    ' not found, error({0}): {1}'.
                                    format(e.status, e.data))
                repos_reported_nonexist.append(key)
                continue

            try:
                languages = repository.get_languages()
                print str(languages)
                print repository.language
                print repository.languages_url
            except GithubException as gite:
                scream.log_warning('GithubException while gettings langs in + ' + key +
                                    ' , error({0}): {1}'.
                                    format(e.status, e.data))
                continue

            rowtowrite = []
            iteration_step_count += 1
            rowtowrite.append(str(repository_object.getName()))
            rowtowrite.append(str(repository_object.getOwner()))

            for language in languages:
                rowtowrite.append(language)
                rowtowrite.append(languages[language])

            rlw.writerow(rowtowrite)

            scream.ssay('Finished processing repo: ' + key + '.. moving on... ')

            #del repos[key]
            'Dictionary cannot change size during iteration'
            'TO DO: associated fields purge so GC will finish the job'
            'implement reset() in intelliRepository.py'
            #scream.ssay('(' + key + ' deleted)')

            limit = gh.get_rate_limit()

            scream.ssay('Rate limit (after whole repo is processed): ' +
                        str(limit.rate.limit) +
                        ' remaining: ' + str(limit.rate.remaining))

            reset_time = gh.rate_limiting_resettime
            reset_time_human_readable = (datetime.datetime.fromtimestamp(
                                         int(reset_time)).strftime(
                                         '%Y-%m-%d %H:%M:%S')
                                         )
            scream.ssay('Rate limit reset time is exactly: ' +
                        str(reset_time) + ' which means: ' +
                        reset_time_human_readable)

            if limit.rate.remaining < 15:
                freeze_more()
