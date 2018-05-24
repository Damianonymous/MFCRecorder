from webapp import app
import flask
import classes

def init_data(config):
    global CONFIG
    CONFIG = config

def check_login():
    print(flask.session.get('logged_in', None))
    if flask.session.get('logged_in', None) is None:
        return flask.redirect(flask.url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if flask.request.method == 'POST':
        if (flask.request.form['username'] != CONFIG.settings.username
                or not classes.helpers.verify_password(flask.request.form['password'], CONFIG.settings.password)):
            error = 'Invalid username/password'
        else:
            flask.session['logged_in'] = True
            flask.flash('Successfully logged in!', 'success')
            return flask.redirect(flask.url_for('start_page'))
    return flask.render_template('login.html', error=error)

@app.route('/logout')
def logout():
    flask.session.pop('logged_in', None)
    return flask.redirect(flask.url_for('start_page'))

@app.route('/')
def start_page():
    return check_login() or flask.render_template(
        'start_page.html', recording=classes.recording.RecordingThread.currently_recording_models,
        wanted=CONFIG.filter.wanted.dict,
        condition_text=classes.helpers.condition_text)

@app.route('/MFC/wanted', methods=['GET', 'POST'])
def wanted():
    check = check_login()
    if check is not None:
        return check

    if flask.request.method == 'POST':
        CONFIG.filter.wanted.set_dict(flask.request.form)

    return flask.render_template('wanted.html', wanted=CONFIG.filter.wanted.dict)

@app.route('/MFC/config', methods=['GET', 'POST'])
def config():
    check = check_login()
    if check is not None:
        return check

    if flask.request.method == 'POST':
        #special treatment for password
        #form data is immutable dict, we want to edit that here
        #dict(form) would give us a list of values per key (since it allows multiple values per key)
        #when iterating over form.items(), we only get the first entry per key, so we do that here
        #(mutliple entries for bool values, since they always send False and only additionally True)
        dict_ = {key:value for key, value in flask.request.form.items()}
        print(dict_)
        old = dict_.pop('password0')
        pw1 = dict_.pop('password1')
        pw2 = dict_.pop('password2')
        if old != '':
            if not classes.helpers.verify_password(old, CONFIG.settings.password):
                flask.flash('wrong old password, new password not set', 'danger')
            elif pw1 != pw2:
                flask.flash('new passwords didn\'t match, new password not set', 'danger')
            elif pw1 == '':
                flask.flash('new password is empty, not setting new password', 'danger')
            else:
                dict_['web:password'] = classes.helpers.hash_password(pw1)

        CONFIG.update(dict_)
        flask.flash('settings have been saved', 'success')

    return flask.render_template('config.html', config=CONFIG)

@app.route('/MFC/add', methods=['GET'])
def add():
    return check_login() or add_or_remove(_add)

def _add(uid, name):
    result = CONFIG.filter.wanted.add(uid, name)
    if result is None:
        flask.flash('{} with uid {} successfully added'.format(name, uid), 'success')
    else:
        flask.flash('{} with uid {} already in wanted list (named "{}")'.format(name, uid, result['custom_name']), 'info')

@app.route('/MFC/remove', methods=['GET'])
def remove():
    return check_login() or add_or_remove(_remove)

def _remove(uid, name):
    result = CONFIG.filter.wanted.remove(uid)
    if result is not None:
        flask.flash('{} with uid {} (named "{}") successfully removed'.format(name, uid, result['custom_name']), 'success')
    else:
        flask.flash('{} with uid {} not in wanted list'.format(name, uid), 'info')

def add_or_remove(action):
    uid_or_name = classes.helpers.try_eval(flask.request.args['uid_or_name'])
    result = classes.models.get_model(uid_or_name)
    if result is None:
        flask.flash('uid or name "{}" not found'.format(uid_or_name), 'danger')
    else:
        action(*result)
    return flask.redirect(flask.url_for('start_page'))

@app.route('/MFC/thumbnails/<uid>')
def thumbnail(uid):
    #TODO: this might take very long and caching would probably be a good idea
    uid = int(uid)
    #try to get thumbnail from current video
    result = classes.helpers.get_live_thumbnail(
        uid, classes.recording.RecordingThread.currently_recording_models.get(uid, {}).get('camserv'))
    if result is None:
        #fallback to avatar from mfc
        result = classes.helpers.get_avatar(uid)
    if result is not None:
        mimetype, img = result
        return flask.send_file(img, mimetype=mimetype)
    return flask.abort(404)
