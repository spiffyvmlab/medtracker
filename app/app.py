from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import time
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://meduser:medpass@db/medtracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    min_interval = db.Column(db.Integer, nullable=False)
    max_doses_per_day = db.Column(db.Integer, nullable=False)

class DoseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    medication = db.relationship('Medication', backref=db.backref('doses', lazy=True))

# Retry loop for database initialization
print("Connecting to:", app.config['SQLALCHEMY_DATABASE_URI'])
max_tries = 10
for i in range(max_tries):
    try:
        with app.app_context():
            db.create_all()
        print("Tables created")
        break
    except OperationalError as e:
        print(f"Database not ready ({e}), retrying in 3s... ({i+1}/{max_tries})")
        time.sleep(3)
else:
    print("Failed to connect to the database after several attempts.")
    exit(1)

@app.route('/', methods=['GET', 'POST'])
def index():
    meds = Medication.query.all()
    med_status = []
    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    for med in meds:
        # Get all dose times for this medication, sorted ascending
        dose_times = [d.timestamp for d in DoseLog.query.filter_by(medication_id=med.id).order_by(DoseLog.timestamp.asc()).all()]
        next_dose_time = calculate_next_dose_time(dose_times, med.min_interval, med.max_doses_per_day, now)
        if now >= next_dose_time:
            next_dose_display = "Now"
        else:
            ndt_date = next_dose_time.date()
            ndt_time = next_dose_time.strftime("%H:%M")
            if ndt_date == today and next_dose_time > now:
                next_dose_display = f"today at {ndt_time}"
            elif ndt_date == tomorrow:
                next_dose_display = f"tomorrow at {ndt_time}"
            else:
                next_dose_display = next_dose_time.strftime("%Y-%m-%d %H:%M")
        last_dose = DoseLog.query.filter_by(medication_id=med.id).order_by(DoseLog.timestamp.desc()).first()
        med_status.append((med, last_dose, next_dose_display))
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Medication Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style id="theme-style">
        body { font-family: sans-serif; margin: 10px; background: #181818; color: #eee; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 4px; border: 1px solid #444; text-align: left; }
        th { background: #222; }
        a, input[type="submit"] { font-size: 1em; color: #8cf; }
        .server-time {
            position: absolute;
            top: 10px;
            right: 20px;
            font-size: 1.1em;
            color: #aaa;
        }
        .toggle-btn {
            margin: 20px 0 10px 0;
            padding: 6px 16px;
            border-radius: 6px;
            border: none;
            background: #333;
            color: #eee;
            font-size: 1em;
            cursor: pointer;
        }
        @media (max-width: 600px) {
            table, thead, tbody, th, td, tr { display: block; }
            th { position: absolute; left: -9999px; top: -9999px; }
            tr { margin-bottom: 10px; border-bottom: 2px solid #222; }
            td { border: none; position: relative; padding-left: 50%; min-height: 30px;}
            td:before {
                position: absolute;
                left: 6px;
                width: 45%;
                white-space: nowrap;
                font-weight: bold;
            }
            td:nth-of-type(1):before { content: "Name"; }
            td:nth-of-type(2):before { content: "Min Interval (hrs)"; }
            td:nth-of-type(3):before { content: "Max Doses/Day"; }
            td:nth-of-type(4):before { content: "Last Taken"; }
            td:nth-of-type(5):before { content: "Next Allowed"; }
            td:nth-of-type(6):before { content: "Actions"; }
            td:nth-of-type(7):before { content: "Dose History"; }
        }
    </style>
</head>
<body>
<div class="server-time" data-utc="{{ now.strftime('%Y-%m-%dT%H:%M:%SZ') }}">
    Server time: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}
</div>
<button class="toggle-btn" id="theme-toggle">Switch to Light Mode</button>
<h1>Medication Tracker</h1>
<a href="/add_med">Add Medication</a>
<table>
    <tr>
        <th>Name</th>
        <th>Min Interval (hrs)</th>
        <th>Max Doses/Day</th>
        <th>Last Taken</th>
        <th>Next Allowed</th>
        <th>Actions</th>
        <th>Dose History</th>
    </tr>
    {% for med, last_dose, next_dose_display in med_status %}
    <tr>
        <td>{{ med.name }}</td>
        <td>{{ med.min_interval }}</td>
        <td>{{ med.max_doses_per_day }}</td>
        <td>
            {% if last_dose %}
                <span class="utc-datetime" data-utc="{{ last_dose.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') }}">{{ last_dose.timestamp }}</span>
            {% else %}
                Never
            {% endif %}
        </td>
        <td><b>{{ next_dose_display }}</b></td>
        <td>
            <a href="/take_dose/{{ med.id }}">Take Dose</a>
            |
            <a href="/add_past_dose/{{ med.id }}">Add Past Dose</a>
            |
            <form action="{{ url_for('delete_med', med_id=med.id) }}" method="post" style="display:inline;" onsubmit="return confirm('Delete this medication and all its history?');">
                <button type="submit" style="background:none;border:none;color:#d00;cursor:pointer;">Delete Med</button>
            </form>                      
        </td>
        <td>
            <a href="/med_history/{{ med.id }}">View</a>
        </td>
    </tr>
    {% endfor %}
</table>
<script>
document.addEventListener("DOMContentLoaded", function() {
    // Convert all UTC datetimes to local time
    document.querySelectorAll('.utc-datetime').forEach(function(el) {
        let utcString = el.dataset.utc;
        if (utcString) {
            let date = new Date(utcString);
            if (!isNaN(date)) {
                el.textContent = date.toLocaleString();
            }
        }
    });
    // Convert server time
    let st = document.querySelector('.server-time');
    if (st && st.dataset.utc) {
        let date = new Date(st.dataset.utc);
        if (!isNaN(date)) {
            st.textContent = "Your time: " + date.toLocaleString();
        }
    }

    // Theme toggle logic
    const darkCSS = `
        body { font-family: sans-serif; margin: 10px; background: #181818; color: #eee; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 4px; border: 1px solid #444; text-align: left; }
        th { background: #222; }
        a, input[type="submit"] { font-size: 1em; color: #8cf; }
        .server-time {
            position: absolute;
            top: 10px;
            right: 20px;
            font-size: 1.1em;
            color: #aaa;
        }
        .toggle-btn {
            margin: 20px 0 10px 0;
            padding: 6px 16px;
            border-radius: 6px;
            border: none;
            background: #333;
            color: #eee;
            font-size: 1em;
            cursor: pointer;
        }
        @media (max-width: 600px) {
            table, thead, tbody, th, td, tr { display: block; }
            th { position: absolute; left: -9999px; top: -9999px; }
            tr { margin-bottom: 10px; border-bottom: 2px solid #222; }
            td { border: none; position: relative; padding-left: 50%; min-height: 30px;}
            td:before {
                position: absolute;
                left: 6px;
                width: 45%;
                white-space: nowrap;
                font-weight: bold;
            }
            td:nth-of-type(1):before { content: "Name"; }
            td:nth-of-type(2):before { content: "Min Interval (hrs)"; }
            td:nth-of-type(3):before { content: "Max Doses/Day"; }
            td:nth-of-type(4):before { content: "Last Taken"; }
            td:nth-of-type(5):before { content: "Next Allowed"; }
            td:nth-of-type(6):before { content: "Actions"; }
            td:nth-of-type(7):before { content: "Dose History"; }
        }
    `;
    const lightCSS = `
        body { font-family: sans-serif; margin: 10px; background: #fff; color: #222; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 4px; border: 1px solid #ccc; text-align: left; }
        th { background: #f0f0f0; }
        a, input[type="submit"] { font-size: 1em; color: #06c; }
        .server-time {
            position: absolute;
            top: 10px;
            right: 20px;
            font-size: 1.1em;
            color: #555;
        }
        .toggle-btn {
            margin: 20px 0 10px 0;
            padding: 6px 16px;
            border-radius: 6px;
            border: none;
            background: #eee;
            color: #222;
            font-size: 1em;
            cursor: pointer;
        }
        @media (max-width: 600px) {
            table, thead, tbody, th, td, tr { display: block; }
            th { position: absolute; left: -9999px; top: -9999px; }
            tr { margin-bottom: 10px; border-bottom: 2px solid #eee; }
            td { border: none; position: relative; padding-left: 50%; min-height: 30px;}
            td:before {
                position: absolute;
                left: 6px;
                width: 45%;
                white-space: nowrap;
                font-weight: bold;
            }
            td:nth-of-type(1):before { content: "Name"; }
            td:nth-of-type(2):before { content: "Min Interval (hrs)"; }
            td:nth-of-type(3):before { content: "Max Doses/Day"; }
            td:nth-of-type(4):before { content: "Last Taken"; }
            td:nth-of-type(5):before { content: "Next Allowed"; }
            td:nth-of-type(6):before { content: "Actions"; }
            td:nth-of-type(7):before { content: "Dose History"; }
        }
    `;
    const styleTag = document.getElementById('theme-style');
    const toggleBtn = document.getElementById('theme-toggle');
    let darkMode = true;

    function setTheme(dark) {
        styleTag.innerHTML = dark ? darkCSS : lightCSS;
        toggleBtn.textContent = dark ? "Switch to Light Mode" : "Switch to Dark Mode";
        darkMode = dark;
        localStorage.setItem('medtracker-theme', dark ? 'dark' : 'light');
    }

    // Load theme from localStorage
    const savedTheme = localStorage.getItem('medtracker-theme');
    if (savedTheme === 'light') {
        setTheme(false);
    } else {
        setTheme(true);
    }

    toggleBtn.addEventListener('click', function() {
        setTheme(!darkMode);
    });
});
</script>
</body>
</html>''', med_status=med_status, DoseLog=DoseLog, now=now)

@app.route('/med_history/<int:med_id>')
def med_history(med_id):
    med = Medication.query.get_or_404(med_id)
    doses = DoseLog.query.filter_by(medication_id=med.id).order_by(DoseLog.timestamp.asc()).all()
    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    dose_times = [d.timestamp for d in doses]
    next_dose_time = calculate_next_dose_time(dose_times, med.min_interval, med.max_doses_per_day, now)
    if now >= next_dose_time:
        next_dose_display = "Now"
    else:
        ndt_date = next_dose_time.date()
        ndt_time = next_dose_time.strftime("%H:%M")
        if ndt_date == today and next_dose_time > now:
            next_dose_display = f"today at {ndt_time}"
        elif ndt_date == tomorrow:
            next_dose_display = f"tomorrow at {ndt_time}"
        else:
            next_dose_display = next_dose_time.strftime("%Y-%m-%d %H:%M")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dose History for {{ med.name }}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; margin: 10px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px 4px; border: 1px solid #ccc; text-align: left; }
            th { background: #f0f0f0; }
            .next-dose { font-size: 1.5em; margin-bottom: 20px; color: #333; }
            .server-time {
                position: absolute;
                top: 10px;
                right: 20px;
                font-size: 1.1em;
                color: #555;
            }
            @media (max-width: 600px) {
                table, thead, tbody, th, td, tr { display: block; }
                th { position: absolute; left: -9999px; top: -9999px; }
                tr { margin-bottom: 10px; border-bottom: 2px solid #eee; }
                td { border: none; position: relative; padding-left: 50%; min-height: 30px;}
                td:before {
                    position: absolute;
                    left: 6px;
                    width: 45%;
                    white-space: nowrap;
                    font-weight: bold;
                }
                td:nth-of-type(1):before { content: "Timestamp"; }
            }
        </style>
    </head>
    <body>
    <div class="server-time" data-utc="{{ now.strftime('%Y-%m-%dT%H:%M:%SZ') }}">
        Server time: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}
    </div>
    <h1>Dose History for {{ med.name }}</h1>
    <div class="next-dose">
        You can take this medication again {{ "Now" if next_dose_display == "Now" else "at " + next_dose_display }}
    </div>
    <a href="/">Back to Medications</a>
    {% if doses %}
    <table>
        <tr><th>Timestamp</th><th>Actions</th></tr>
        {% for dose in doses %}
        <tr>
            <td class="utc-datetime" data-utc="{{ dose.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') }}">{{ dose.timestamp }}</td>
            <td>
                <a href="{{ url_for('edit_dose', dose_id=dose.id) }}">Edit</a>
                |
                <form action="{{ url_for('delete_dose', dose_id=dose.id) }}" method="post" style="display:inline;" onsubmit="return confirm('Delete this dose?');">
                    <button type="submit" style="background:none;border:none;color:#d00;cursor:pointer;">Delete</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No doses recorded for this medication.</p>
    {% endif %}
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll('.utc-datetime').forEach(function(el) {
            let utcString = el.dataset.utc;
            if (utcString) {
                let date = new Date(utcString); // Do NOT add + "Z"
                if (!isNaN(date)) {
                    el.textContent = date.toLocaleString();
                }
            }
        });
        let st = document.querySelector('.server-time');
        if (st && st.dataset.utc) {
            let date = new Date(st.dataset.utc); // Do NOT add + "Z"
            if (!isNaN(date)) {
                st.textContent = "Your time: " + date.toLocaleString();
            }
        }
    });
    </script>
    </body>
    </html>
    ''', med=med, doses=doses, next_dose_display=next_dose_display, now=now)

@app.route('/edit_dose/<int:dose_id>', methods=['GET', 'POST'])
def edit_dose(dose_id):
    dose = DoseLog.query.get_or_404(dose_id)
    med = dose.medication
    if request.method == 'POST':
        timestamp_str = request.form['timestamp']
        try:
            dose.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")
            db.session.commit()
            return redirect(url_for('med_history', med_id=med.id))
        except ValueError:
            return "Invalid date/time format. <a href='/'>Back</a>"
    return render_template_string('''
        <html><body>
        <h1>Edit Dose for {{ med.name }}</h1>
        <form method="post" id="edit-dose-form">
            Date and Time: <input type="datetime-local" name="timestamp" id="edit-dose-datetime" required><br>
            <input type="submit" value="Update Dose">
        </form>
        <a href="{{ url_for('med_history', med_id=med.id) }}">Back</a>
        <script>
        document.addEventListener("DOMContentLoaded", function() {
            var utcString = "{{ dose.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') }}";
            var date = new Date(utcString);
            if (!isNaN(date)) {
                var pad = n => n.toString().padStart(2, '0');
                var local = date.getFullYear() + '-' +
                            pad(date.getMonth() + 1) + '-' +
                            pad(date.getDate()) + 'T' +
                            pad(date.getHours()) + ':' +
                            pad(date.getMinutes());
                document.getElementById('edit-dose-datetime').value = local;
            }
            document.getElementById('edit-dose-form').addEventListener('submit', function(e) {
                var input = document.getElementById('edit-dose-datetime');
                var localDate = new Date(input.value);
                if (!isNaN(localDate)) {
                    input.value = localDate.toISOString().slice(0,16);
                    console.log("Converted to UTC:", input.value);
                }
            });
        });
        </script>
        </body></html>
    ''', med=med, dose=dose)

@app.route('/delete_dose/<int:dose_id>', methods=['POST'])
def delete_dose(dose_id):
    dose = DoseLog.query.get_or_404(dose_id)
    med_id = dose.medication_id
    db.session.delete(dose)
    db.session.commit()
    return redirect(url_for('med_history', med_id=med_id))

@app.route('/delete_med/<int:med_id>', methods=['POST'])
def delete_med(med_id):
    med = Medication.query.get_or_404(med_id)
    # Delete all associated doses first
    DoseLog.query.filter_by(medication_id=med.id).delete()
    db.session.delete(med)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_med', methods=['GET', 'POST'])
def add_med():
    if request.method == 'POST':
        name = request.form['name']
        min_interval = int(request.form['min_interval'])
        max_doses_per_day = int(request.form['max_doses_per_day'])
        new_med = Medication(name=name, min_interval=min_interval, max_doses_per_day=max_doses_per_day)
        db.session.add(new_med)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template_string('''<html><body><h1>Add Medication</h1>
    <form method="post">
        Name: <input type="text" name="name"><br>
        Min Interval (hrs): <input type="number" name="min_interval"><br>
        Max Doses Per Day: <input type="number" name="max_doses_per_day"><br>
        <input type="submit" value="Add">
    </form>
    <a href="/">Back</a></body></html>''')

@app.route('/take_dose/<int:med_id>')
def take_dose(med_id):
    med = Medication.query.get_or_404(med_id)
    now = datetime.utcnow()
    # Rolling 24-hour window logic for max doses
    window_start = now - timedelta(hours=24)
    doses_24h = DoseLog.query.filter(
        DoseLog.medication_id == med.id,
        DoseLog.timestamp >= window_start
    ).order_by(DoseLog.timestamp.asc()).all()
    if len(doses_24h) >= med.max_doses_per_day:
        return "Max doses reached in the last 24 hours. <a href='/'>Back</a>"
    last_dose = DoseLog.query.filter_by(medication_id=med.id).order_by(DoseLog.timestamp.desc()).first()
    if last_dose and (now - last_dose.timestamp).total_seconds() < med.min_interval * 3600:
        return "Minimum interval not met. <a href='/'>Back</a>"
    dose = DoseLog(medication_id=med.id)
    db.session.add(dose)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_past_dose/<int:med_id>', methods=['GET', 'POST'])
def add_past_dose(med_id):
    med = Medication.query.get_or_404(med_id)
    if request.method == 'POST':
        timestamp_str = request.form['timestamp']
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            return "Invalid date/time format. <a href='/'>Back</a>"
        dose = DoseLog(medication_id=med.id, timestamp=timestamp)
        db.session.add(dose)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template_string('''
        <html><body>
        <h1>Add Past Dose for {{ med.name }}</h1>
        <form method="post" id="add-dose-form">
            Date and Time: <input type="datetime-local" name="timestamp" id="add-dose-datetime" required><br>
            <input type="submit" value="Add Dose">
        </form>
        <script>
        document.getElementById('add-dose-form').addEventListener('submit', function(e) {
            var input = document.getElementById('add-dose-datetime');
            var localDate = new Date(input.value);
            if (!isNaN(localDate)) {
                // Convert local time to UTC ISO string (YYYY-MM-DDTHH:MM)
                input.value = localDate.toISOString().slice(0,16);
                console.log("Converted to UTC:", input.value);
            }
        });
        </script>
        </body></html>
    ''', med=med)

def calculate_next_dose_time(dose_times, min_interval, max_doses_per_24h, now):
    """
    dose_times: list of datetime, sorted ascending (oldest first)
    min_interval: hours
    max_doses_per_24h: int
    now: datetime
    """
    if not dose_times:
        return now

    # Check min interval from last dose
    last_dose_time = dose_times[-1]
    next_allowed_by_interval = last_dose_time + timedelta(hours=min_interval)

    # Find all doses in the last 24 hours
    doses_in_24h = [dt for dt in dose_times if dt > now - timedelta(hours=24)]

    if len(doses_in_24h) >= max_doses_per_24h:
        # Next allowed is 24h after the earliest dose in the last 24h window
        next_allowed_by_max = doses_in_24h[0] + timedelta(hours=24)
    else:
        next_allowed_by_max = now

    return max(next_allowed_by_interval, next_allowed_by_max, now)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)