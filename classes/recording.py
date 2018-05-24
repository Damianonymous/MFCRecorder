import threading
import datetime
import os
import livestreamer
from colorama import Fore
import classes.postprocessing as postprocessing
import classes.helpers as helpers

def start_recording(session, settings):
    '''starts recording a session if it is not already being recorded'''
    #possible race condition?
    already_recording = RecordingThread.currently_recording_models.get(session['uid'])
    if already_recording:
        #TODO: recordings based on min_viewers won't get their rc updated here
        already_recording['rc'] = session['rc']
    else:
        RecordingThread(session, settings).start()

class RecordingThread(threading.Thread):
    '''thread for recording a MFC session'''
    URL_TEMPLATE = "hlsvariant://http://video{srv}.myfreecams.com:1935/NxServer/ngrp:mfc_{id}.f4v_mobile/playlist.m3u8"
    READING_BLOCK_SIZE = 1024
    currently_recording_models = {}
    total_data = 0
    file_count = 0
    _lock = threading.Lock()

    def __init__(self, session, config):
        super().__init__()
        self.file_size = 0
        self.session = session
        self.config = config
        self.currently_recording_models[session['uid']] = session
        print(Fore.GREEN + "started recording {}".format(self.session['nm']) + Fore.RESET)

    def run(self):
        stream = self.stream
        if not stream:
            return

        start_time = datetime.datetime.now()
        file_path = self.create_path(self.config.settings.directory_structure, start_time)
        self.session['dl_path'] = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with self._lock:
            self.file_count += 1

        with stream.open() as source, open(file_path, 'wb') as target:
            while self.config.keep_recording(self.session):
                try:
                    target.write(source.read(self.READING_BLOCK_SIZE))
                except:
                    break
                with self._lock:
                    self.total_data += self.READING_BLOCK_SIZE
                self.file_size += self.READING_BLOCK_SIZE

        if self.file_size == 0:
            with self._lock:
                self.file_count -= 1
            os.remove(file_path)

        elif self.config.settings.post_processing_command:
            postprocessing.put_item(self.config.settings.post_processing_command,
                                    self.session['uid'], self.session['nm'], file_path)

        elif self.config.settings.completed_directory:
            directory = self.create_path(self.config.settings.completed_directory, start_time)
            os.makedirs(directory, exist_ok=True)
            os.rename(file_path, os.path.join(directory, os.path.basename(file_path)))

        self.currently_recording_models.pop(self.session['uid'], None)
        print(Fore.RED + "{}'s session has ended".format(self.session['nm']) + Fore.RESET)

    @property
    def stream(self):
        '''returns a dictionary with available streams'''
        streams = {} #not sure this is needed for the finally to work
        try:
            streams = livestreamer.Livestreamer().streams(self.URL_TEMPLATE.format(
                id=int(self.session['uid']) + 100_000_000,
                srv=int(self.session['camserv']) - 500))
        finally:
            return streams.get('best')

    def create_path(self, template, time):
        '''builds a recording-specific path from a template'''
        return template.format(
            path=self.config.settings.save_directory, model=self.session['nm'], uid=self.session['uid'],
            seconds=time.strftime("%S"), day=time.strftime("%d"),
            minutes=time.strftime("%M"), hour=time.strftime("%H"),
            month=time.strftime("%m"), year=time.strftime("%Y"),
            auto='{}_'.format(helpers.condition_text(self.session['condition'], self.session.get('condition-text'), True)))
