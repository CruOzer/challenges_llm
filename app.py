import os
import json
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, abort
import logging

from jinja2 import Environment

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File to store challenge data
DATA_FILE = 'challenge_data.json'

logging.basicConfig(filename='app.log', level=logging.DEBUG)


# Define the custom Jinja2 filter
def calculate_completed_days(progress):
    return sum(1 for day_completed in progress.values() if day_completed)



# Register the custom filter with Flask's Jinja2 environment
app.jinja_env.filters['calculate_completed_days'] = calculate_completed_days


# Function to load challenge data from the JSON file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}


# Function to save challenge data to the JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Load challenge data on app startup
challenges = load_data()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_challenge', methods=['POST'])
def start_challenge():
    try:
        challenge_name = request.form['challenge_name'].strip()  # Trim the challenge name
        start_date_str = request.form['start_date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')  # Adjust the format accordingly

        duration = int(request.form['duration'])

        # Create a dictionary for daily progress, initially set to False
        progress = {}
        for i in range(duration):
            day = start_date + timedelta(days=i)
            progress[day.strftime('%Y-%m-%d')] = False

        challenges[challenge_name] = {
            'duration': duration,
            'start_date': start_date_str,
            'progress': progress
        }

        flash(f'Started a {duration}-day challenge: {challenge_name}', 'success')
        # Save the updated challenge data
        save_data(challenges)
    except (ValueError, KeyError):
        flash('Invalid input. Please check your data and try again.', 'danger')
    return redirect(url_for('index'))



@app.route('/challenges')
def list_challenges():
    current_date = datetime.now().date()  # Aktuelles Datum
    challenge_statuses = {}  # Dictionary, um die Status für jede Challenge zu speichern

    sorted_challenges= dict(sorted(challenges.items(), key=lambda x: datetime.strptime(x[1]['start_date'], '%Y-%m-%d').date()))
    # Sortiere die Challenges nach Startdatum aufsteigend
    active_challenges = {}  # Dictionary für aktive Challenges

    for challenge, details in sorted_challenges.items():
        start_date = datetime.strptime(details['start_date'], '%Y-%m-%d').date()
        if current_date < start_date:
            status = 'Not Started'
            active_challenges[challenge] = details
        else:
            completed_days = calculate_completed_days(details['progress'])
            progress_percent = (completed_days / details['duration']) * 100
            rounded_percent = round(progress_percent, 2)
            if progress_percent == 100:
                status = 'Done'
            else:
                status = f'In Progress ({rounded_percent}%)'
                active_challenges[challenge] = details

        challenge_statuses[challenge] = status

    show_completed = False  # Hier können Sie die Bedingung basierend auf Ihren Anforderungen festlegen

    return render_template('challenges.html', challenges=active_challenges, challenge_statuses=challenge_statuses,
                           show_completed=show_completed)


@app.route('/challenge_details/<challenge_name>')
def challenge_details(challenge_name):
    # Hier sollten Sie den Challenge-Namen verwenden, um die entsprechenden Details aus Ihren Daten abzurufen
    challenge_details = challenges.get(challenge_name)

    if challenge_details:
        return render_template('challenge_details.html', challenge_name=challenge_name, challenge_details=challenge_details)
    else:
        # Handle error for challenge not found
        return render_template('error.html', message='Challenge not found'), 404


@app.route('/update_daily_progress/<challenge_name>/<date>', methods=['POST'])
def update_daily_progress(challenge_name, date):
    try:
        completed = request.form.get('completed') == 'on'
        challenges[challenge_name]['progress'][date] = completed
        flash(f'Updated progress for {challenge_name} on {date}', 'success')
        # Save the updated challenge data
        save_data(challenges)
    except KeyError:
        flash('Challenge or date not found.', 'danger')
        # Redirect to the challenge details page for the same challenge
    return redirect(url_for('challenge_details', challenge_name=challenge_name))


@app.route('/update_progress/<challenge_name>', methods=['POST'])
def update_progress(challenge_name):
    try:
        # Get the updated progress for each day from the form
        updated_progress = request.form.getlist('progress')

        if challenge_name in challenges:
            # Update progress for each day based on the order in the form
            for i, day_progress in enumerate(updated_progress):
                challenges[challenge_name]['progress'][i] = day_progress == 'on'

            flash(f'Updated progress for {challenge_name}', 'success')
            # Save the updated challenge data
            save_data(challenges)
        else:
            abort(404)  # Challenge not found, return a 404 error
    except ValueError:
        flash('Invalid progress. Please enter a valid number.', 'danger')

    return redirect(url_for('list_challenges'))

@app.route('/delete_challenge/<challenge_name>', methods=['POST'])
def delete_challenge(challenge_name):
    try:
        # Überprüfen, ob die Challenge existiert
        if challenge_name in challenges:
            del challenges[challenge_name]
            flash(f'Deleted challenge: {challenge_name}', 'success')
            # Speichern Sie die aktualisierten Challenge-Daten
            save_data(challenges)
        else:
            flash('Challenge not found.', 'danger')
    except Exception as e:
        flash(f'Error deleting challenge: {str(e)}', 'danger')
    return redirect(url_for('list_challenges'))

@app.route('/completed_challenges')
def completed_challenges():
    current_date = datetime.now().date()  # Aktuelles Datum
    challenge_statuses = {}  # Dictionary, um die Status für jede Challenge zu speichern

    sorted_challenges = dict(
    sorted(challenges.items(), key=lambda x: datetime.strptime(x[1]['start_date'], '%Y-%m-%d').date()))
    # Sortiere die Challenges nach Startdatum aufsteigend
    completed_challenges = {}  # Dictionary für aktive Challenges

    for challenge, details in sorted_challenges.items():
            completed_days = calculate_completed_days(details['progress'])
            progress_percent = (completed_days / details['duration']) * 100
            rounded_percent = round(progress_percent, 2)
            if rounded_percent == 100:
                status = 'Done'
                completed_challenges[challenge] = details
                challenge_statuses[challenge] = status
    show_completed = True  # Hier können Sie die Bedingung basierend auf Ihren Anforderungen festlegen

    return render_template('challenges.html', challenges=completed_challenges,
                           challenge_statuses=challenge_statuses, show_completed=show_completed)


# Custom error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
