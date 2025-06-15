const socket = new WebSocket(`ws://${window.location.host}/ws/hl7-monitor/`);

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const row = document.querySelector(`#message-${data.message.id}`);

    if (!row) {
        // Add new row to table
        const table = document.querySelector('table tbody');
        table.prepend(createMessageRow(data.message));
    } else {
        // Update existing row
        row.querySelector('.status').textContent = data.message.status;
        row.querySelector('.status').className = `text-${data.message.status === 'ERROR' ? 'danger' : 'success'}`;
    }
};

function createMessageRow(msg) {
    const tr = document.createElement('tr');
    tr.id = `message-${msg.id}`;
    tr.innerHTML = `
        <td><a href="/hl7-monitor/message/${msg.id}/">${msg.timestamp}</a></td>
        <td>${msg.type}</td>
        <td>IN</td>
        <td class="text-${msg.status === 'ERROR' ? 'danger' : 'success'}">${msg.status}</td>
        <td>0.000s</td>
    `;
    return tr;
}