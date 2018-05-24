import threading
import queue
import subprocess
import os

def init_workers(count):
    '''create the specified amount of workers'''
    [PostprocessingThread().start() for i in range(0, count)]

def put_item(command, uid, name, path):
    '''add an item to the postprocessing queue'''
    directory, filename = os.path.split(path)
    PostprocessingThread.work.put(command.split() + [path, filename, directory, name, uid])

class PostprocessingThread(threading.Thread):
    '''a thread to perform post processing work'''
    work = queue.Queue()

    def run(self):
        while True:
            item = self.work.get(block=True)
            subprocess.call(item)
            self.work.task_done()
