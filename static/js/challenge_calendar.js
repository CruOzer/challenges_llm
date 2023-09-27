function createChallengeCalendar(challengeName, startDate, duration, progressData) {
    var calendarEl = document.getElementById('calendar_' + challengeName);
    // Startdatum und Dauer der Challenge
    var startDate = new Date(startDate);
    var endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + duration - 1);

    var events = [
        // Mark Start Date
        {
            title: 'Start Date',
            start: startDate,
            color: 'blue',
        },
        // Mark End Date
        {
            title: 'End Date',
            start: endDate,
            color: 'blue',
        }
    ];

    // Konvertieren Sie die progressData in ein Array von Ereignissen
    for (var date in progressData) {
        if (progressData.hasOwnProperty(date)) {
            var completed = progressData[date];
            var event = {
                title: completed ? 'Completed' : 'Not Completed',
                start: date,
                color: completed ? 'green' : 'red'
            };
            events.push(event);
        }
    }

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: events
    });
    calendar.render();
}
