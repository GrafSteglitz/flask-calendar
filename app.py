from flask import Flask, render_template, request, redirect, session, g, url_for
from forms import EventForm, RegistrationForm, LoginForm, CalendarViewForm, EditEventForm
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
# from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta, date, time
from helpers import build_calendar, str_to_date_obj, str_to_time_obj
from functools import wraps
from copy import deepcopy
from json import loads

"""
username: catman
password: password
/calendar is the main page for viewing events
"""

app = Flask(__name__)
app.config["SECRET_KEY"] = "brian-the-dinosaur"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.teardown_appcontext(close_db)

@app.errorhandler(404)
def handle_bad_request(e):
    # this code is from https://flask.palletsprojects.com/en/stable/errorhandling/
    return f"""bad request from \
        last referring page: {request.referrer}""", 404

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)
    g.db_date_format = '%Y%m%d'

@app.context_processor
def load_nav():
    d = {'index':'Home','show_events':'Events List','calendar':'Calendar','logout':'Logout','create_event':'Create an Event'}
    dt = date.today()
    user = ''
    if 'user_id' in session.keys() and session['user_id']:
        user = session['user_id'] 
    return dict(nav=d,dt=dt,user=user)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login",next=request.url))
        return view(*args,**kwargs)
    return wrapped_view

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        clash = db.execute("""
            SELECT * FROM users WHERE user_id = ?;""",(user_id,)).fetchone()
        if clash is not None:
            form.user_id.errors.append("User name already taken!")
        else:
            db.execute("""
                       INSERT INTO users (user_id, password) VALUES (?,?);""", (user_id, generate_password_hash(password)))
            db.commit()
            return redirect(url_for("login"))
    return render_template("register.html",form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if request.method=="POST":
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user_in_db = db.execute("""
            SELECT * FROM users
            WHERE user_id =?;""",(user_id,)).fetchone()
        if user_in_db is None:
            e_list = [a for a in form.user_id.errors]
            e_list.append("No such user name!")
            form.user_id.errors = tuple(e_list)
        elif not check_password_hash(user_in_db["password"], password):
            e_list = [a for a in form.user_id.errors]
            e_list.append("Incorrect password!")
            form.user_id.errors = tuple(e_list)
        else:
            session.clear()
            session["user_id"] = user_id
            session["active_datetime"] = datetime.now()
            session.modified = True
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("login.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return redirect(url_for("index"))

@app.route("/create_event", methods=["GET","POST"])
@login_required
def create_event():
    form = EventForm()
    message = ""

    if form.validate_on_submit():
        
        values = {'user_id': session["user_id"],'name':form.name.data,'description':form.description.data,'start_date':form.start_date.data,
                  'end_date':form.end_date.data,'start_time':form.start_time.data,'end_time':form.end_time.data,
                  'location':form.location.data,'participants':form.participants.data,
                  'repeats': form.repeats.data, 'repeat_frequency': form.repeat_frequency.data,'series_id':''}
        
        
        if values['start_time']:
            d = values['start_time']
            values['start_time'] = d.strftime('%H:%M')
        if values['end_time']:
            d = values['end_time']
            values['end_time'] = d.strftime('%H:%M')
        if not values['repeat_frequency']:
            values['repeat_frequency'] = -1

        
        db = get_db()
        query = """SELECT series_id FROM events;"""
        results = db.execute(query).fetchall()
        results = [a[0] for a in results]
        results = set(results)

        
        events_list = [values]
        # code to populate repeating events
        if values['repeats'] > 1 and values['repeat_frequency'] > 0:
            repeats = 1
            jump = values['repeat_frequency']
            while repeats <= values['repeats']:
                # date objects
                new_event = deepcopy(values)
                new_event['start_date'] = new_event['start_date'] + timedelta(days=jump*repeats)
                new_event['start_date'] = new_event['start_date'].strftime(f'{g.db_date_format}')
                new_event['end_date'] = new_event['end_date'] + timedelta(days=jump*repeats)
                new_event['end_date'] = new_event['end_date'].strftime(f'{g.db_date_format}')

                clash = [a for a in list(results) if a]
                series_code = max(clash)+1 if clash else 1
                new_event['series_id'] = series_code
                events_list.append(new_event)
                repeats +=1
            
        if values['start_date']:
            d = values['start_date']
            values['start_date'] = d.strftime(f'{g.db_date_format}')
        if values['end_date']:
            d = values['end_date']
            values['end_date'] = d.strftime(f'{g.db_date_format}')
        db = get_db()
        # messages = []
        for each in events_list:
            query = """INSERT INTO Events (user_id, name, description, start_date, end_date, start_time, end_time, location, participants, series_id)
            VALUES (?,?,?,?,?,?,?,?,?,?);
            """
            insertions = (each['user_id'],each['name'],each['description'],each['start_date'],each['end_date'],each['start_time'],each['end_time'],\
                each['location'],each['participants'],each['series_id'])
            db.execute(query, insertions)
            db.commit()
            message = "Data successfully committed!"
            # messages.append("Data successfully committed!")

    dt = datetime.now()
    form.start_date.data = date.today()
    form.start_time.data = time(dt.hour, dt.minute)
    form.end_date.data = date.today()
    last_hour_row = dt.hour+1 if dt.hour+1 < 24 else dt.hour
    form.end_time.data = time(last_hour_row, dt.minute)
    form.repeats.data = 1
    form.repeat_frequency.data = 0
    
        
    return render_template("create_event.html",form=form, message=message)

@app.route("/show_events", methods=["GET","POST"])
@login_required
def show_events():
    # SHOW A SIMPLE HTML TABLE OF RECORDED EVENTS
    # query = """SELECT * FROM Events;"""
    # db = get_db()
    # c = db.cursor()
    # results = c.execute(query).fetchall()
    # colnames = [col[0] for col in c.description]
    
    # results = db.execute(query).fetchall()
    query = """SELECT * FROM Events WHERE user_id=?;"""
    db = get_db()
    c = db.cursor()
    param = (session["user_id"],)
    results = c.execute(query,param).fetchall()
    colnames = [col[0] for col in c.description]
    
    return render_template('show_events.html',colnames=colnames, results=results)

@app.route("/delete_event", methods=["GET","POST"])
@login_required
def delete_event():
    # print(request.referrer)
    if request.method =="POST":
        # delete_id = ''
        delete_id = request.form['id']
        db = get_db()
        query = """DELETE FROM Events WHERE user_id=? AND id=?;"""
        db.execute(query,(session['user_id'],delete_id))
        db.commit()
        print("Deletion successful!")
    
    if request.referrer:
        return redirect(request.referrer)
    
    return render_template("index.html")

@app.route("/delete_series", methods=["GET","POST"])
@login_required
def delete_series():
    # print(request.referrer)
    if request.method =="POST":
        # delete_id = ''
        delete_id = request.form['series_id']
        if delete_id:
            db = get_db()
            query = """DELETE FROM Events WHERE user_id=? AND series_id=?;"""
            db.execute(query,(session['user_id'],delete_id))
            db.commit()
            print("Deletion successful!")
    
    if request.referrer:
        return redirect(request.referrer)
    
    return render_template("index.html")

@app.route("/today", methods=["POST","GET"])
@login_required
def today():
    if request.method=="POST":
        tdy = date.today()
        tdy = tdy.strftime(f'{g.db_date_format}')
        mode = request.form.get('mode')
        return redirect(url_for('calendar',start=tdy,mode=mode))
    return redirect(url_for('calendar'))

@app.route("/form_handler", methods=["POST"])
@login_required
def form_handler():
    # this view modifies the session variables mode and user_date and redirects to '/calendar'
    
    # check if there is form data
    if request.method == "POST":
        form = CalendarViewForm()
        mode = None
        start_day = None
        
        if form.view_select.data:
            mode = form.view_select.data

        if form.date_select.data:
            start_day = form.date_select.data.strftime(f'{g.db_date_format}')

        if not mode or not start_day:
            return redirect(url_for('calendar'))
    
        return redirect(url_for('calendar',start=start_day,mode=mode))

@app.route("/add_week_month", methods=["POST"])
@login_required
def add_week_month():
    mode = request.form.get('mode')
    interval = request.form.get('interval')
    d = request.form.get('current_date')
    d = d.split('-')
    d.reverse()
    d = ''.join(d)
    d  = str_to_date_obj(d)

    if interval == "week":
        d = d + timedelta(days=7)
    elif interval=="month":
        m = d.month + 1
        if m == 13:
            m = 1
        d = date(day=d.day,month=m,year=d.year)
    else:
        d = d + timedelta(days=1)
    
    start_day = d.strftime(f'{g.db_date_format}')
    
    return redirect(url_for('calendar',start=start_day,mode=mode,interval=interval))

@app.route("/remove_week_month", methods=["POST"])
@login_required
def remove_week_month():
    interval = request.form.get('interval')
    mode = request.form.get('view_select')
    d = request.form.get('current_date')
    d = d.split('-')
    d.reverse()
    d = ''.join(d)
    d  = str_to_date_obj(d)
    
    if interval == "week":
        d = d - timedelta(days=7)
    elif interval=="month":
        m = d.month -1
        if m == 0:
            m = 12
        d = date(day=d.day,month=m,year=d.year)
    else:
        d = d - timedelta(days=1)

    start_day = d.strftime(f'{g.db_date_format}')
    
    return redirect(url_for('calendar',start=start_day,mode=mode, interval=interval))

@app.route("/edit_event",methods=["GET","POST"])
@login_required
def edit_event():
    
    id = request.form.get('id') if request.form.get('id') else request.args.get('id')
    form = EditEventForm()
    query = """SELECT * FROM Events WHERE id=?;"""
    previous_errors = request.args.get('errors')
    errors = loads(previous_errors.replace("'","\"")) if previous_errors else {}
    db = get_db()
    c = db.cursor()
    results = c.execute(query,(id,)).fetchone()
    colnames = [col[0] for col in c.description]
    results = dict(zip(colnames, [a for a in results]))
    form.name.data = results['name']
    form.description.data = results['description']
    form.start_date.data = str_to_date_obj(results['start_date'])
    form.end_date.data = str_to_date_obj(results['end_date'])
    form.start_time.data = str_to_time_obj(results['start_time'])
    form.end_time.data = str_to_time_obj(results['end_time'])
    form.location.data = results['location']
    form.participants.data = results['participants']
    form.id.data = id
    
    return render_template('edit_event.html',form=form, errors=errors)
    return redirect(url_for('calendar'))

@app.route("/update_event",methods=["POST"])
@login_required
def update_event():
    form = EditEventForm()
    if not form.validate_on_submit():
        return redirect(url_for('edit_event',errors=form.errors,id=form.id.data))
    query = """UPDATE Events SET name=?, description=?, start_date=?, end_date=?, start_time=?, end_time=?, location=?,
    participants=? WHERE id=?;"""
    params = (form.name.data,form.description.data,form.start_date.data.strftime(f'{g.db_date_format}'),form.end_date.data.strftime(f'{g.db_date_format}'),\
              form.start_time.data.strftime('%H:%M'),form.end_time.data.strftime('%H:%M'),form.location.data,\
              form.participants.data,form.id.data)
    db = get_db()
    db.execute(query,params)
    db.commit()
    return redirect(url_for('calendar'))

@app.route("/calendar", methods=["GET","POST"])
@login_required
# @cal_wrapper
def calendar():
    # SHOW THE CALENDAR VIEW WITH EVENTS
    
    """
    variables:
    user_date: stored in session
    mode = week/month (passed by CalendarViewForm to /calendar)
    """
    form = CalendarViewForm()
    # tday_form = TodayForm()
    
    results = ""
    user_date = date.today()
    mode=form.view_select.data
    if request.args.get('start'):
        user_date = request.args.get('start')
        year=user_date[0:4]
        month=user_date[4:6]
        day=user_date[6:8]
        # year, month, day
        user_date = date(day=int(day),month=int(month),year=int(year))
    
    if request.args.get('mode'):
        mode = request.args.get('mode')

    

    range_end = 6
    range_start = user_date
    if mode == 'month':
        # set first display date to first day of month
        # range_start = date(user_date.year,user_date.month,1)
        # y = 1
        # # find the first Monday of the month
        # while range_start.strftime('%A') != 'Monday':
        #     range_start = date(range_start.year,range_start.month,y)
        #     y+=1
        # # only look at four weeks
        
        # month_end = range_start + timedelta(days=1)
        # f = 1
        # while month_end.month == range_start.month:
        #     month_end = range_start + timedelta(days=f)
        #     f+=1
        range_end = 28
    
    week_end = range_start + timedelta(days=range_end)

    # HEADER TO SHOW AT TOP OF PAGE
    date_header = range_start.strftime('%A %d %b %Y')+ ' to ' + week_end.strftime('%A %d %b %Y')
    hours = list(range(0,24))
    start_query = range_start.strftime(f'{g.db_date_format}')
    end_query = week_end.strftime(f'{g.db_date_format}')
    # get events by user_id
    query = """SELECT * FROM Events WHERE user_id=? AND start_date>=? AND end_date <=?;"""
    db = get_db()
    c = db.cursor()
    results = c.execute(query,(session['user_id'],start_query,end_query)).fetchall()
    col_names = [col[0] for col in c.description]
    
    # list of user's events
    event_list = []
    
    for row in results:
        event_list.append(dict(zip(col_names, [a for a in row])))

    # min_time = hours[0]
    # max_time = hours[-1]
    # for e in event_list:
    #     st = str_to_time_obj(e['start_time'])
    #     et = str_to_time_obj(e['end_time'])
    #     if st.hour < min_time and min_time > 1:
    #         min_time = st.hour
    #     if et.hour > max_time and max_time < 23:
    #         max_time = et.hour
    
    # hours = list(range(min_time,max_time))

    day_list = [range_start]
    
    # create date objects for the entire week

    x = 0
    while x < range_end:
        new_date = day_list[0]+ timedelta(days=x+1)
        day_list.append(new_date)
        x+=1

    html = build_calendar(day_list, event_list, hours)
    form.date_select.data = user_date
    form.view_select.data = mode
    dropdown = {'day':'Day','week':'Week','month':'Month'}
    selected=None
    if request.args.get('interval'):
        selected = request.args.get('interval')
    else:
        selected = "week"

    dropdown_html = ""
    for k in dropdown.keys():
        select_html = f"<option value=\"{k}\""
        if k == selected:
            select_html+= " selected=\"True\""
        select_html += f">{dropdown[k]}</option>"
        dropdown_html += select_html
    return render_template('calendar.html',html=html, date_header=date_header,\
    form=form,range_start=range_start.strftime('%d-%m-%Y'),dropdown_html=dropdown_html)


if __name__=='__main__':
    app.run(debug=True)