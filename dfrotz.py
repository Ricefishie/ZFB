# abstraction layer for dfrotz
# parts for non-blocking communication are taken from
# https://gist.github.com/EyalAr/7915597
# modified for heroku

import os
import Queue
import subprocess
import sys
import threading
from subprocess import PIPE, Popen
import stat

class DFrotz():
    def __init__(self, arg_frotz_path, arg_game_path):
        self.frotz_path = arg_frotz_path
        self.game_path = arg_game_path
        print(self.frotz_path)
        print(self.game_path)
        st = os.stat('./tools/dfrotz')
	os.chmod('./tools/dfrotz', st.st_mode | stat.S_IEXEC)
	args = self.game_path
        #print(os.path.abspath(self.frotz_path))
        try:
            self.frotz = Popen(
                args,
                executable = self.frotz_path,
                shell=True,
                stdin=PIPE,
                stdout=PIPE,
                  
                bufsize=1        
            )
        except OSError as e:
            print('Couldn\'t run Frotz. Maybe wrong architecture?')
            print e.errno
            print e.filename
            print e.strerror

            sys.exit(0)
        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self.enqueue, args=(self.frotz.stdout, self.queue))
        self.thread.daemon = True
        self.thread.start()

    def enqueue(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def send(self, command):
        print(command) 
        #.encode('cp1252'))
        try:
            self.frotz.stdin.write(command+'\n')
            self.frotz.stdin.flush()
        except IOError as e:
            print(e)
            debug_string = '[DEV] Pipe is broken. Please tell @mrtnb what you did.'
            
            return debug_string

    def generate_output(self):
        self.raw_output = ''.join(self.lines)

        # clean up Frotz' output
        self.output = self.raw_output.replace('> > ', '')
        self.output = self.output.replace('\n.\n', '\n\n')

        return self.output

    def get(self):
        self.lines = []
        while True:
            try:
                self.line = self.queue.get(timeout=1)#.decode('cp1252')
                self.line = '\n'.join(' '.join(line_.split()) for line_ in self.line.split('\n'))
            except Queue.Empty:
                print('EMPTY QUEUE')
                break
            else:
                self.lines.append(self.line)

        for index, line in enumerate(self.lines):
            # long line (> 70 chars) could be a part of
            # a text passage - removing \n there to
            # make output more readable
            if len(line) >= 70 and line.endswith('\n'):
                self.lines[index] = line.replace('\n', ' ')

        return self.generate_output()

def main():
    f = DFrotz()

    while True:
        print(f.get())
        cmd = '%s\r\n' % input()
        f.send(cmd)

if __name__ == '__main__':
    main()
