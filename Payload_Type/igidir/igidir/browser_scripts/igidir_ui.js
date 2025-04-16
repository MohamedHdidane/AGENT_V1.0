// Custom UI rendering for IGIDIR agent
function renderIGIDIRTaskTable(data, row, col, cell) {
    var task = data[row].task;
    var display = data[row].display;
    
    if (col === "command") {
        if (task.command === "process_inject") {
            return "<span class='badge badge-danger'>" + task.command + "</span>";
        } else if (task.command === "cred_harvest") {
            return "<span class='badge badge-warning'>" + task.command + "</span>";
        } else if (task.command === "persistence") {
            return "<span class='badge badge-success'>" + task.command + "</span>";
        }
    }
    
    if (col === "display_params") {
        if (task.command === "process_inject") {
            return "<code>" + display + "</code>";
        }
        return display;
    }
    
    return cell;
}

$(document).ready(function() {
    // Register our custom renderer
    if (typeof registerTaskTableRenderer === "function") {
        registerTaskTableRenderer(renderIGIDIRTaskTable);
    }
    
    // Add custom UI elements
    $('#taskCommandDropdown').append(
        '<div class="dropdown-divider"></div>' +
        '<h6 class="dropdown-header">IGIDIR Commands</h6>' +
        '<a class="dropdown-item" href="#" onclick="taskCommandSelect(\'process_inject\')">Process Injection</a>' +
        '<a class="dropdown-item" href="#" onclick="taskCommandSelect(\'cred_harvest\')">Credential Harvest</a>' +
        '<a class="dropdown-item" href="#" onclick="taskCommandSelect(\'persistence\')">Persistence</a>'
    );
});