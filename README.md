# README

## Running the Service

### Locally
To run the service locally, first make the virtual environment:
```bash
    python3 -m venv venv
```
Then, activate it:
```bash
    source venv/bin/activate
```
Once inside the vitual environment, start the endpoint by the following:
```bash
    python3 main.py
```
You may then issue commands to add records:
```bash
curl -X POST http://localhost:8000/ingest \       
  -H 'Content-Type: application/json' \
  -d '{
    "device_id": "dev-2",
    "timestamp": "2025-09-09T17:00:00Z",
    "data_payload": { "gene_count": 12, "sample_quality": 0.98 }
```
As well as check the contentd of the *buffer_db* of *recordings* databases via (resp):
```bash
    curl -s http://localhost:8000/check-buffer | jq .
```
```bash
    curl -s http://localhost:8000/records | jq .
```

### Docker
To run the service via docker, first build it:
```bash
    docker build -t tester .
```
Then run it:
```bash
    docker run -p 8000:8000 tester 
```
From which point one may interact with it with identical curl commands as in the local running. 

## Scalability Strategy
To address scalability, it is first important to consider if the entire service is being handled by multiple machines or a single machine. This is relevant as the solution space changes considerably

### Multiple Machines (Horizontal Scaling)
This case may be thought of crudely though accurately as throwing resources at the problem. If there were concerns of a single machine being overloaded with requests, simply providing more machines to handle the requese immediately reduce the load of the existing machines. 

Practically, how this could work is defining a mapping from sets of devices (those which produdce and report records) to particular machines, acting as the *POST/ingest* endpoints. To enable fault tolerance (of a machine endpoint), each of the devices should have knowledge of other machines which they may report their records to in the case of machine failure. This provides additional simple load balancing by its very nature. 

On the other side, each machine endpoint could then report their records to some master database. This could occur via cloud infrastructure e.g. S3/Lambda functions or another phsyical "master" endpoint. Though I would recommend the former. How the reporting occurs (e.g. stream or batch uploads) should be determined in accordance with the architecture chosen. For an S3/Lambda function, batching is more cost efficient due to mandatory memory mediums on AWS.

### Single Machine (Vertical Scaling)
If all records are being reported to a single machine, then there is more work to be done. 

If the machine were to become overburdened, this can lead to failed requests and retries, and eventual cascaded failures. A classic solution to this problem is to implement exponential backoff, where reporting machines delay subsequent reports exponentially on incurring repeated failures.  

## A Note about DoS
In a system like this, an immediate concern to security and availability would be denial of service (DoS) attacks. This could be mounted by an adversary by simply flooding reports to the endpoint with the intention of overloading it leading to service failure and preventing genuine reports from being processed. 

While this is a natural concern it is also easily mitigated. Permissioned access to the system via tokenized access is an elegant solution. However, it is more likely that a permissioned network, one not accessible to users not on it, would also be both stronger and simpler. It is a typical solution within the manufacturing industry hoping to achieve the same architecture/goals.

## Observability

