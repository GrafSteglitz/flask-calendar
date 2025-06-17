from database import get_db
# import json
from datetime import date, time, datetime, timedelta
from flask import url_for

def shift_right(input_list):
    last_item = input_list.pop(len(input_list)-1)
    input_list.insert(0,last_item)
    return input_list

def get_events(date1,date2):
    db = get_db()
    query = f"""SELECT * FROM Events WHERE start_date >= '{date1}' AND end_date <= '{date2}';"""
    events = db.execute(query).fetchall()
    return events

def date_dict(dt_obj):
    if not dt_obj:
        return None
    d = {'day':-1,'month':-1,'year':-1}
    d['day']=dt_obj.day
    d['month']=dt_obj.hour
    d['year']=dt_obj.year
    return dt_obj

def render_time(t):
    t = int(t)
    if t < 10:
        t = '0'+str(t)
    return t

def date_dict(d_time_obj):
    try:
        out_d = {'day':d_time_obj.day,'month': d_time_obj.month,'year': d_time_obj.year}
        return out_d
    except:
        return None

def date_obj_to_str(date_obj):
    
    try:
        out_str = date_obj.strftime('%d-%m-%Y')
        return out_str
    except:
        return None

def str_to_date_obj(s):
    # s = s.split('-')
    year = int(s[0:4])
    month = int(s[4:6])
    day = int(s[6:8])
    
    d = date(day=day,month=month,year=year)
    return d
    
def time_dict(time_obj):
    try:
        out_d = {'hour':time_obj.hour,'minute': time_obj.minute}
        return out_d
    except:
        return None

def str_to_time_obj(s):
    s = s.split(":")
    s = [int(a) for a in s]
    t = time(*s)
    return t

def get_td_pcs(st,et):
    # offset, duration, offset
    pcs = [0,0,0]
    # if the event begins at the start of the hour, set the first offset to 0
    if st['minute']== 0:
        pcs[0] = 0
        pcs[1] = 100
    # if the event begins after the start of the hour and finishes after the hour
    if st['minute'] > 0 and et['hour']>st['hour']:
        pcs[1] = (st['minute']/60)*100
        pcs[0] = (60-st['minute'])*100
    # if the event starts during the hour and ends before the end of the hour
    if st['minute'] > 0 and et['hour']==st['hour']:
        offset1 = 60-(et['minute']-st['minute'])
        duration = et['minute']-st['minute']
        offset2 = 60-offset1-duration
        pcs[0] = offset1
        pcs[1] = duration
        pcs[2] = offset2
        pcs = [(a/60)*100 if a else a for a in pcs]
    
    return tuple(pcs)

def build_calendar(day_list,event_list, hours_range):
    
    # BUILD HTML TABLE
    html = "<table class=\"calendar\"><tr><th></th>"
    # build the first row with col names
    for day in day_list:
            html += f"<th"
            if day.weekday() == 5 or day.weekday() == 6:
                html+=" class=\"weekend\""
            html += f">{day.strftime('%a %d')}</th>"
    html += "</tr>"

    # build table row by row (rows=hours, cols=days)
    for hour in hours_range:
        s = "<tr>"
        s += f"<th>{hour}</th>"
        for day in day_list:
            s += "<td>"
            for e in event_list:
                current_datetime = datetime(day=day.day,month=day.month, year=day.year, hour=hour)
                if e['name'] == "Huge fight":
                    pass
                st = str_to_time_obj(e['start_time'])
                sd = str_to_date_obj(e['start_date'])
                # CHECK AGAINST DATETIME OBJECTS RATHER THAN USING IF STATEMENTS BELOW???
                start_datetime = datetime(day=sd.day,month=sd.month,year=sd.year,hour=st.hour)
                et = str_to_time_obj(e['end_time'])
                ed = str_to_date_obj(e['end_date'])
                end_datetime = datetime(day=ed.day,month=ed.month,year=ed.year,hour=et.hour)
                
                def continuance():
                    # return f"<div class=\"event\">({e['name']})</div>"
                    return "<div class=\"event\">.</div>"
                if start_datetime == current_datetime:
                    s += f"""<div class=\"event\"><span class='title'>{e['name']}
                        {e['start_time']}-{e['end_time']}</span><br/>
                        {e['description']}</div>
                        <form class='edit' action='{url_for('edit_event')}' method='post' novalidate>
                        <input type='hidden' name = 'id' value='{e['id']}'/>
                        <input type='hidden' name = 'series_id' value='{e['series_id']}' />
                        <input type ='submit' value ='View event'/>
                        <input type='submit' value='Delete Event' formaction='{url_for('delete_event')}'/>"""
                    if e['series_id']:
                        s+= f"<input type='submit' value='Delete Series' formaction='{url_for('delete_series')}'/>"
                    s+=    "<br/></form>"
                if start_datetime < current_datetime < end_datetime:
                    s+= continuance()
                if current_datetime == end_datetime - timedelta(hours=1):
                    s+= f"<div class=\"event\">{e['name']}(END)</div>"
                # # WRITE THE EVENT HEADER
                # if (st.hour == hour and sd.day == day.day):
                    
                #     s += f"<div class=\"event\"><span>{e['name']}\
                #         {e['start_time']}-{e['end_time']}</span></div>"
                # # if the event starts at an hour before the time ranges shown
                # if (st.hour < hours_range[0] and hour == hours_range[0] and sd.day == day.day):
                #     s += f"<div class=\"event\"><span>{e['name']}\
                #         {e['start_time']}-{e['end_time']}</span></div>"

                # # if it is the start day and the end hour has not been reached, print the event name
                # if(sd.day==day.day and hour > st.hour):
                #     s+= continuance()
                
                # # if it is an intervening day between the start day and the end day, but is neither
                # if sd.day < day.day < ed.day:
                #     s+=continuance()

                # # if it is the end day and not the start day and the end hour has not yet been reached
                # if day.day == ed.day and day.day != sd.day and hour < et.hour:
                #     s+=continuance()

                # #print again if the event extends into the end hour on the last day
                # if (day.day == ed.day and hour == et.hour and et.minute > 0):
                #     s += f"<div class=\"event\">({e['name']})</div>"
            s += "</td>" 
        s += "</tr>"
        html += s
    html += "</table>"
    return html

