from prometheus_client import Counter, Histogram, Gauge

# Total de jobs por fila e status
jobs_total = Counter(
    'jobs_total', 
    'Total de jobs processados', 
    ['queue', 'status']
)

# Duração da execução dos jobs
job_duration = Histogram(
    'job_duration_seconds', 
    'Tempo de execução dos jobs', 
    ['queue']
)

# Tamanho atual da DLQ
dlq_size = Gauge(
    'dlq_size', 
    'Quantidade de jobs na Dead Letter Queue', 
    ['queue']
)

# Jobs atualmente em processamento
jobs_running = Gauge(
    'jobs_running', 
    'Jobs sendo processados no momento', 
    ['queue']
)
