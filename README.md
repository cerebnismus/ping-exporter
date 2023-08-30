## ping-exporter

This service provides ICMP ping metrics for Prometheus. Using this [ping](https://github.com/cerebnismus/ping) repository.


## Usage

```python
$ python3 ping-exporter.py --help
usage: ping-exporter.py [-h] [--port PORT] [--interval INTERVAL]
                        [--timeout TIMEOUT] [--count COUNT] [--debug]
```

## Grafana Dashboard

Use the following dashboard to visualize the ping metrics:



## Prometheus Configuration

In the `prometheus.yml` file, add a new scrape config:

```yaml
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

  # Attach these labels to any time series or alerts when communicating with
  # external systems (federation, remote storage, Alertmanager).
  external_labels:
      monitor: 'ping-exporter'

# A scrape configuration containing exactly one endpoint to scrape:
scrape_configs:

  - job_name: 'ping-exporter'
    # metrics_path defaults to '/metrics'
    metrics_path: /metrics
    static_configs:
      - targets:
        - 1.1.1.1
        - 8.8.8.8
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9099  # exporters hostname:port
```
