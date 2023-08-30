from flask import Flask, request, jsonify, render_template_string
import subprocess, threading, schedule, yaml

app = Flask(__name__)

# Run the C program with target IP and number of packets as arguments of function
def run_c_program(target='8.8.8.8', num_packets=4):
    output = subprocess.getoutput(f'sudo ./a.out {target} {num_packets}')
    with open('icmp_c_output.txt', 'w') as f:
        f.write(output)

def run_schedule():
    while True:
        schedule.run_pending()

@app.route('/')
def index():
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    # Convert Python dictionary to YAML formatted string
    config_yaml = yaml.dump(config, default_flow_style=False)

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ping Metrics Exporter</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; }
            .container { background-color: #fff; padding: 20px; margin: 20px; }
            .highlight { background-color: #e4e4e4; padding: 5px; }
            .github-ribbon {
                position: absolute;
                top: 0; right: 0; 
                border: 0;
            }
        </style>
    </head>
    <body>
        <a href="https://github.com/cerebnismus/ping-exporter">
            <img class="github-ribbon" src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/GitHub_forkme_ribbon_right_green.svg/360px-GitHub_forkme_ribbon_right_green.svg.png" alt="Fork me on GitHub">
        </a>
        <div class="container">
            <h1 style="color: green;">Welcome to Ping Metrics Exporter!</h1>
            <p>This service provides ICMP ping metrics for Prometheus.
            Using this <a href="https://github.com/cerebnismus/ping"> ping </a> repository.</p>

            <h2>Configuration:</h2>
            <pre class="highlight">{{ config_yaml }}</pre>
            <h2>Check Metrics:</h2>
            <form action="/metrics" method="get">
                Target: <input type="text" name="target" placeholder="8.8.8.8">
                <input type="submit" value="Go">
            </form>
            <p>Or use predefined targets: 
            {% for target in targets %}
                <a href="/metrics?target={{ target }}">{{ target }}</a>
                {% if not loop.last %}, {% endif %}
            {% endfor %}
            </p>
        </div>
    </body>
    </html>
    '''
    # return render_template_string(template, config=config, targets=targets)
    return render_template_string(template, config_yaml=config_yaml, targets=targetz)

@app.route('/metrics')
def metrics():
    target = request.args.get('target', default='8.8.8.8', type=str)
    output = subprocess.getoutput(f'sudo ./a.out {target} 4')

    # Extracting metrics from output last line:
    last_line = output.split('\n')[-1]
    last_line = last_line.split(', ')
    ping_packets_transmitted = last_line[0].split(' ')[0]
    ping_packets_received = last_line[1].split(' ')[0]
    
    ping_packets_loss_percent = last_line[2].split(' ')[0]
    ping_packets_loss_percent = ping_packets_loss_percent[:-1] # remove %

    ping_rtt_ms = last_line[3].split(' ')[1]
    ping_rtt_ms = ping_rtt_ms[:-2]  # remove ms from ping_rtt_ms
    
    ping_node_status = 1 
    if ping_packets_received == 0 or ping_packets_loss_percent == 100:
        ping_node_status = 0

    # Creating Prometheus metrics format with what contain config file after the metrics:
    # Logs for the ping:
    # {output}
    output_to_metrics = f'''
# HELP ping_packets_transmitted Number of packets transmitted
# TYPE ping_packets_transmitted gauge
ping_packets_transmitted {ping_packets_transmitted}
# HELP ping_packets_received Number of packets received
# TYPE ping_packets_received gauge
ping_packets_received {ping_packets_received}
# HELP ping_packets_loss_percent Percentage of packets loss
# TYPE ping_packets_loss_percent gauge
ping_packets_loss_percent {ping_packets_loss_percent}
# HELP ping_rtt_ms Round trip time in milliseconds
# TYPE ping_rtt_ms gauge
ping_rtt_ms {ping_rtt_ms}
# HELP ping_node_status Node status 1 is for up
# TYPE ping_node_status gauge
ping_node_status {ping_node_status}
'''
# Module configuration:
# {config}

    Response = app.response_class
    return Response(output_to_metrics, content_type='text/plain; charset=utf-8')


if __name__ == '__main__':

    # options from config.yml
    with open('config.yml', 'r') as f:  # Load config
        config = yaml.safe_load(f)

    # targets from /etc/prometheus/prometheus.yml
    with open('/etc/prometheus/prometheus.yml', 'r') as f:
        prometheus_config = yaml.safe_load(f)
    for job in prometheus_config.get('scrape_configs', []):
        if job.get('job_name') == 'ping-exporter':
            targetz = job.get('static_configs', [{}])[0].get('targets', [])

    # select targets, where job name is ping-exporter
    for target in targetz:  # runs for every target in config
        schedule.every(config['options']['interval']).minutes.do(run_c_program, target=target, num_packets=config['options']['num_packets'])
        t = threading.Thread(target=run_schedule)
        t.start()

    print(" * Interval:", config['options']['interval'])
    print(" * Number of packets:", config['options']['num_packets'])
    print(" * Targets:", targetz)
    app.run(host='0.0.0.0', port=9099)
