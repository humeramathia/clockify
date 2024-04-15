// Load users into the dropdown when the page loads
document.addEventListener('DOMContentLoaded', function () {
    loadUsers();
    loadProjects();
});

function loadUsers() {
    fetch('http://localhost:7145/clockify/users')
        .then(response => response.json())
        .then(userNames => {
            const userDropdown = document.getElementById('userDropdown');
            userDropdown.innerHTML = '<option value="">Choose User</option>';
            userNames.forEach(userName => {
                const option = document.createElement('option');
                option.value = userName;
                option.textContent = userName;
                userDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching users:', error));
}

function loadProjects() {
    fetch('http://localhost:7145/clockify/projects/names')
        .then(response => response.json())
        .then(projectNames => {
            const projectDropdown = document.getElementById('projectDropdown');
            projectDropdown.innerHTML = '<option value="">Select Project</option>';
            projectNames.forEach(projectName => {
                const option = document.createElement('option');
                option.value = projectName;
                option.textContent = projectName;
                projectDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading projects:', error));
}

// Handle project selection change to load tasks
document.getElementById('projectDropdown').addEventListener('change', function (event) {
    const projectName = event.target.value;
    loadTasksForProject(projectName);
});

function loadTasksForProject(projectName) {
    const encodedProjectName = encodeURIComponent(projectName);
    fetch(`http://localhost:7145/clockify/projects/${encodeURIComponent(projectName)}/tasks`)
        .then(response => response.json())
        .then(taskNames => {
            const taskDropdown = document.getElementById('taskDropdown');
            taskDropdown.innerHTML = '<option value="">Select Task</option>';
            taskNames.forEach(taskName => {
                const option = document.createElement('option');
                option.value = taskName;
                option.textContent = taskName;
                taskDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading tasks:', error));
}

