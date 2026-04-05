from flask import Flask, render_template_string, request, jsonify
import platform
import datetime
import os
import psutil

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EC2 Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #333; }
        .navbar { background: linear-gradient(135deg, #232f3e, #37475a); padding: 16px 32px; color: white; display: flex; align-items: center; justify-content: space-between; }
        .navbar h1 { font-size: 1.4rem; }
        .navbar .status { background: #4caf50; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; }
        .container { max-width: 1000px; margin: 32px auto; padding: 0 16px; }
        .card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 24px; margin-bottom: 24px; }
        .card h2 { font-size: 1.1rem; color: #232f3e; margin-bottom: 16px; border-bottom: 2px solid #ff9900; padding-bottom: 8px; display: inline-block; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .metric { background: #f9fafb; border-radius: 8px; padding: 16px; text-align: center; }
        .metric .value { font-size: 1.8rem; font-weight: bold; color: #232f3e; }
        .metric .label { font-size: 0.85rem; color: #666; margin-top: 4px; }
        .bar-bg { background: #e0e0e0; border-radius: 4px; height: 8px; margin-top: 8px; }
        .bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #ff9900, #ffb84d); }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
        th { background: #f5f5f5; font-weight: 600; }
        .task-section { margin-top: 16px; }
        .task-input { display: flex; gap: 8px; margin-bottom: 16px; }
        .task-input input { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.95rem; }
        .task-input button { padding: 10px 20px; background: #ff9900; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; }
        .task-input button:hover { background: #e68a00; }
        .task-list { list-style: none; }
        .task-list li { padding: 10px 14px; background: #f9fafb; margin-bottom: 6px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
        .task-list li .delete-btn { background: #e74c3c; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
        footer { text-align: center; padding: 24px; color: #999; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>EC2 Server Dashboard</h1>
        <span class="status">● Running</span>
    </div>
    <div class="container">
        <div class="card">
            <h2>System Information</h2>
            <table>
                <tr><th>Hostname</th><td>{{ info.hostname }}</td></tr>
                <tr><th>Platform</th><td>{{ info.platform }}</td></tr>
                <tr><th>Architecture</th><td>{{ info.architecture }}</td></tr>
                <tr><th>Python Version</th><td>{{ info.python_version }}</td></tr>
                <tr><th>Server Time</th><td>{{ info.server_time }}</td></tr>
                <tr><th>Uptime</th><td>{{ info.uptime }}</td></tr>
            </table>
        </div>
        <div class="card">
            <h2>Resource Usage</h2>
            <div class="grid">
                <div class="metric">
                    <div class="value">{{ info.cpu_percent }}%</div>
                    <div class="label">CPU Usage</div>
                    <div class="bar-bg"><div class="bar-fill" style="width: {{ info.cpu_percent }}%"></div></div>
                </div>
                <div class="metric">
                    <div class="value">{{ info.memory_percent }}%</div>
                    <div class="label">Memory Usage</div>
                    <div class="bar-bg"><div class="bar-fill" style="width: {{ info.memory_percent }}%"></div></div>
                </div>
                <div class="metric">
                    <div class="value">{{ info.disk_percent }}%</div>
                    <div class="label">Disk Usage</div>
                    <div class="bar-bg"><div class="bar-fill" style="width: {{ info.disk_percent }}%"></div></div>
                </div>
                <div class="metric">
                    <div class="value">{{ info.total_memory_gb }} GB</div>
                    <div class="label">Total Memory</div>
                </div>
            </div>
        </div>
        <div class="card">
            <h2>Task Board</h2>
            <div class="task-section">
                <div class="task-input">
                    <input type="text" id="taskInput" placeholder="Add a new task...">
                    <button onclick="addTask()">Add</button>
                </div>
                <ul class="task-list" id="taskList"></ul>
            </div>
        </div>
    </div>
    <footer>&copy; {{ info.year }} EC2 Dashboard &mdash; Running on Flask</footer>
    <script>
        let tasks = [];
        function renderTasks() {
            const list = document.getElementById('taskList');
            list.innerHTML = tasks.map((t, i) =>
                `<li>${t} <button class="delete-btn" onclick="deleteTask(${i})">Delete</button></li>`
            ).join('');
        }
        function addTask() {
            const input = document.getElementById('taskInput');
            const text = input.value.trim();
            if (!text) return;
            fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task: text})
            }).then(r => r.json()).then(data => { tasks = data.tasks; renderTasks(); });
            input.value = '';
        }
        function deleteTask(index) {
            fetch('/api/tasks/' + index, {method: 'DELETE'})
                .then(r => r.json()).then(data => { tasks = data.tasks; renderTasks(); });
        }
        document.getElementById('taskInput').addEventListener('keypress', e => { if (e.key === 'Enter') addTask(); });
        fetch('/api/tasks').then(r => r.json()).then(data => { tasks = data.tasks; renderTasks(); });
    </script>
</body>
</html>
"""

task_store = []


def get_system_info():
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "hostname": platform.node(),
        "platform": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": round(mem.percent, 1),
        "disk_percent": round(disk.percent, 1),
        "total_memory_gb": round(mem.total / (1024 ** 3), 2),
        "year": datetime.datetime.now().year,
    }


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, info=get_system_info())


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": task_store})


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json()
    task = data.get("task", "").strip()
    if task:
        task_store.append(task)
    return jsonify({"tasks": task_store})


@app.route("/api/tasks/<int:index>", methods=["DELETE"])
def delete_task(index):
    if 0 <= index < len(task_store):
        task_store.pop(index)
    return jsonify({"tasks": task_store})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
