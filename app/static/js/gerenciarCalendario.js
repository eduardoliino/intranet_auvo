// app/static/js/gerenciarCalendario.js

document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const eventModal = new bootstrap.Modal(document.getElementById('eventModal'));
    const form = document.getElementById('eventForm');
    const eventTitleInput = document.getElementById('eventTitle');
    const eventStartInput = document.getElementById('eventStart');
    const eventEndInput = document.getElementById('eventEnd');
    const eventDescriptionInput = document.getElementById('eventDescription');
    const eventLocationInput = document.getElementById('eventLocation');
    const eventColorInput = document.getElementById('eventColor');
    const eventIdInput = document.getElementById('eventId');
    const deleteButton = document.getElementById('deleteEventButton');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/admin/calendario/eventos',
        editable: true,
        selectable: true,

        select: function(info) {
            form.reset();
            eventIdInput.value = '';
            eventTitleInput.value = '';
            eventStartInput.value = info.startStr.slice(0, 16);
            eventEndInput.value = info.endStr.slice(0, 16);
            deleteButton.classList.add('d-none');
            document.getElementById('modalTitle').innerText = 'Adicionar Novo Evento';
            eventModal.show();
        },

        eventClick: function(info) {
            eventIdInput.value = info.event.id;
            eventTitleInput.value = info.event.title;
            eventStartInput.value = info.event.startStr.slice(0, 16);
            eventEndInput.value = info.event.end ? info.event.endStr.slice(0, 16) : '';
            eventDescriptionInput.value = info.event.extendedProps.description || '';
            eventLocationInput.value = info.event.extendedProps.location || '';
            eventColorInput.value = info.event.backgroundColor || '#3788d8';
            deleteButton.classList.remove('d-none');
            document.getElementById('modalTitle').innerText = 'Editar Evento';
            eventModal.show();
        },

        eventDrop: function(info) {
            updateEvent(info.event);
        },

        eventResize: function(info) {
            updateEvent(info.event);
        }
    });

    calendar.render();

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const eventData = {
            id: eventIdInput.value,
            title: eventTitleInput.value,
            start: eventStartInput.value,
            end: eventEndInput.value,
            description: eventDescriptionInput.value,
            location: eventLocationInput.value,
            color: eventColorInput.value
        };

        const url = eventData.id ? `/admin/calendario/eventos/editar/${eventData.id}` : '/admin/calendario/eventos/novo';
        const method = eventData.id ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                calendar.refetchEvents();
                eventModal.hide();
            } else {
                alert('Erro ao guardar o evento.');
            }
        });
    });

    deleteButton.addEventListener('click', function() {
        const eventId = eventIdInput.value;
        if (eventId && confirm('Tem a certeza de que deseja apagar este evento?')) {
            fetch(`/admin/calendario/eventos/remover/${eventId}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    calendar.refetchEvents();
                    eventModal.hide();
                } else {
                    alert('Erro ao apagar o evento.');
                }
            });
        }
    });

    function updateEvent(event) {
        const eventData = {
            id: event.id,
            title: event.title,
            start: event.start.toISOString(),
            end: event.end ? event.end.toISOString() : null,
            description: event.extendedProps.description,
            location: event.extendedProps.location,
            color: event.backgroundColor
        };

        fetch(`/admin/calendario/eventos/editar/${event.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                alert('Erro ao atualizar o evento.');
                info.revert();
            }
        });
    }
});