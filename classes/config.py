import configparser
import time
import os
import platform
import ctypes
import json
import threading
import classes.helpers as helpers

LIST_MODE_WANTED = 0
LIST_MODE_BLACKLISTED = 1

class Settings():
    def __init__(self, parser, make_absolute):
        self._make_absolute = make_absolute
        self.conf_save_directory = parser.get('paths', 'save_directory')
        self.conf_wishlist_path = parser.get('paths', 'wishlist_path')
        self.interval = parser.getint('settings', 'check_interval')
        self.directory_structure = parser.get('paths', 'directory_structure').lower()
        self.post_processing_command = parser.get('settings', 'post_processing_command')
        self.post_processing_thread_count = parser.getint('settings', 'post_processing_thread_count')
        self.port = parser.getint('web', 'port')
        self.web_enabled = parser.getboolean('web', 'enabled')
        self.min_space = parser.getint('settings', 'min_space')
        self.conf_completed_directory = parser.get('paths', 'completed_directory').lower()
        self.priority = parser.getint('settings', 'priority')
        self.username = parser.get('web', 'username')
        self.password = parser.get('web', 'password')

        #make save directory so that _get_free_diskspace can work
        os.makedirs(self.save_directory, exist_ok=True)
    
    @property
    def save_directory(self):
        return self._make_absolute(self.conf_save_directory)

    @property
    def wishlist_path(self):
        return self._make_absolute(self.conf_wishlist_path)

    @property
    def completed_directory(self):
        return self._make_absolute(self.conf_completed_directory)

class Filter():
    def __init__(self, parser, settings):
        self.newer_than_hours = parser.getint('auto_recording', 'newer_than_hours')
        self.score = parser.getint('auto_recording', 'score')
        self.auto_stop_viewers = parser.getint('auto_recording', 'auto_stop_viewers')
        self.stop_viewers = parser.getint('settings', 'stop_viewers')
        self.min_tags = max(1, parser.getint('auto_recording', 'min_tags'))
        self._wanted_tags_str = parser.get('auto_recording', 'tags')
        self._update_tags()
        self.tag_stop_viewers = parser.getint('auto_recording', 'tag_stop_viewers')
        #account for when stop is greater than min
        self.min_viewers = max(self.stop_viewers, parser.getint('settings', 'min_viewers'))
        self.viewers = max(self.auto_stop_viewers, parser.getint('auto_recording', 'viewers'))
        self.tag_viewers = max(self.tag_stop_viewers, parser.getint('auto_recording', 'tag_viewers'))

        self.wanted = Wanted(settings)

    @property
    def wanted_tags_str(self):
        return self._wanted_tags_str

    @wanted_tags_str.setter
    def wanted_tags_str(self, value):
        self._wanted_tags_str = value
        self._update_tags()

    def _update_tags(self):
        self.wanted_tags = {s.strip().lower() for s in self._wanted_tags_str.split(',')}

class Config():
    def __init__(self, config_file_path):
        self._lock = threading.Lock()
        self._config_file_path = config_file_path
        self._parser = configparser.ConfigParser()
        self.refresh()

    @property
    def settings(self):
        return self._settings

    @property
    def filter(self):
        return self._filter

    def _make_absolute(self, path):
        if not path or os.path.isabs(path):
            return path
        return os.path.join(os.path.dirname(self._config_file_path), path)

    def refresh(self):
        '''load config again to get fresh values'''
        self._parse()
        self._settings = Settings(self._parser, self._make_absolute)
        self._filter = Filter(self._parser, self.settings)
        self._available_space = self._get_free_diskspace()

    def _parse(self):
        with self._lock:
            self._parser.read(self._config_file_path)

    def update(self, data):
        '''expects a dictionary with section:option as key and the value as value'''
        #will delete comments in the config, but when this method is used, config was edited in webapp,
        #so there are comments there and in the sample config
        with self._lock:
            for key, value in data.items():
                section, option = key.split(':')
                self._parser.set(section, option, value)
            self._write()
        self.refresh()

    def _write(self):
        with open(self._config_file_path, 'w') as target:
            self._parser.write(target)

    #maybe belongs more into a filter class, but then we would have to create one
    def does_model_pass_filter(self, model):
        '''determines whether a recording should start'''
        f = self.filter
        try:
            if f.wanted.is_wanted(model.uid):
                #TODO: do we want a global min_viewers if model specific is not set??
                m_settings = f.wanted.dict[model.uid]
                if model.session['rc'] < max(m_settings['min_viewers'], m_settings['stop_viewers']):
                    return False
                else:
                    model.session['condition'] = helpers.Condition.WANTED
                    return True
            if f.wanted.is_blacklisted(model.uid):
                return False
            if f.wanted_tags:
                matches = f.wanted_tags.intersection(model.tags if model.tags is not None else [])
                if len(matches) >= f.min_tags and model.session['rc'] >= f.tag_viewers:
                    model.session['condition'] = helpers.Condition.TAGS
                    model.session['condition-text'] = ','.join(matches)
                    return True
            if f.newer_than_hours and model.session['creation'] > int(time.time()) - f.newer_than_hours * 60 * 60:
                model.session['condition'] = helpers.Condition.NEW
                return True
            if f.score and model.session['camscore'] > f.score:
                model.session['condition'] = helpers.Condition.SCORE
                return True
            if f.viewers and model.session['rc'] > f.viewers:
                model.session['condition'] = helpers.Condition.VIEWERS
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def _get_free_diskspace(self):
        '''https://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python'''
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(self.settings.save_directory), None, None, ctypes.pointer(free_bytes))
            return free_bytes.value / 1024 / 1024
        st = os.statvfs(self.settings.save_directory)
        return st.f_bavail * st.f_frsize / 1024 / 1024 / 1024

    def keep_recording(self, session):
        '''determines whether a recording should continue'''
        try:
            #would it be possible that no entry is existing if we are already recording?
            #TODO: global stop_viewers if no model specific is set??
            if session['condition'] == helpers.Condition.VIEWERS:
                min_viewers = self.filter.auto_stop_viewers
            elif session['condition'] == helpers.Condition.WANTED:
                min_viewers = self.filter.wanted.dict[session['uid']]['stop_viewers']
            elif session['condition'] == helpers.Condition.TAGS:
                min_viewers = self.filter.tag_stop_viewers
            else:
                min_viewers = 0
            return session['rc'] >= min_viewers and self._available_space > self.settings.min_space
        except Exception as e:
            print(e)
            return True

class Wanted():
    def __init__(self, settings):
        self._lock = threading.RLock()
        self._settings = settings
        #create new empty wanted file
        try:
            with open(self._settings.wishlist_path, 'x') as file:
                file.write('{}')
        except FileExistsError:
            pass
        self._load()

    def _load(self):
        with self._lock:
            with open(self._settings.wishlist_path, 'r+') as file:
                self.dict = {int(uid): data for uid, data in json.load(file).items()}

    def _save(self):
        with open(self._settings.wishlist_path, 'w') as file:
            json.dump(self.dict, file, indent=4)

    def set_dict(self, data):
        '''expects dictionary with uid:key as keys and value as value'''

        #building the new wanted dict
        new = {}
        for key, value in data.items():
            uid, key = key.split(':')
            uid = int(uid)
            #relies on enabled being the first argument that is passed per model, maybe a bit dirty
            if key == 'enabled':
                new[uid] = {}
            print(value)
            new[uid][key] = helpers.try_eval(value)

        with self._lock:
            self.dict = new
            self._save()

    def add(self, uid, custom_name='', list_mode=LIST_MODE_WANTED):
        '''Adds model to dict and returns None. If already existing, returns model settings.'''
        with self._lock:
            settings = self.dict.get(uid)
            if settings is not None:
                return settings
            self._set_data(uid, list_mode=list_mode, custom_name=custom_name)

    def remove(self, uid):
        '''removes model from dict and returns settings, if not existing returns None'''
        with self._lock:
            result = self.dict.pop(uid, None)
            self._save()
            return result

    def _set_data(self, uid, enabled=True, list_mode=LIST_MODE_WANTED,
                 custom_name='', comment='', min_viewers=0, stop_viewers=0, priority=0):
        '''same as _set_data_dict, but takes named arguments instead of a dict'''
        data = {
            'enabled': enabled,
            'list_mode': list_mode,
            'custom_name': custom_name,
            'comment': comment,
            'min_viewers': min_viewers,
            'stop_viewers': stop_viewers,
            'priority': priority,
        }
        with self._lock:
            self._set_data_dict(uid, data)

    def _set_data_dict(self, uid, data):
        '''Set data dictionary for model uid, existing or not'''
        with self._lock:
            self.dict[uid] = data
            self._save()

    def is_wanted(self, uid):
        '''determines if model is enabled and wanted'''
        return self._is_list_mode_value(uid, LIST_MODE_WANTED)

    def is_blacklisted(self, uid):
        '''determines if model is enabled and blacklisted'''
        return self._is_list_mode_value(uid, LIST_MODE_BLACKLISTED)

    def _is_list_mode_value(self, uid, value):
        '''determines if list_mode equals the specified one, but only if the item is enabled'''
        entry = self.dict.get(uid)
        if not (entry and entry['enabled'] and self._settings.priority <= entry['priority']):
            return False
        return entry['list_mode'] == value
