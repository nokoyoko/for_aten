# README

## Running the Service

### Locally
To run the service locally, first make the virtual environment:
```bash
    python3 -m venv venv
```
Then activate it:
```bash
    source venv/bin/activate
```
Flask may then need to be installed...
```bash
    pip install flask
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
    "device_id": "dev-1",
    "timestamp": "2025-09-09T17:00:00Z",
    "data_payload": { "gene_count": 12, "sample_quality": 0.98 }
```
As well as check the contentd of the `buffer_db` of `recordings` databases via (resp):
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
From which point one may interact with it with identical curl commands as above in **Locally**. 

## Design Decisions & Assumptions
The endpoint is designed to be as simple as possible, without sacrificing security. There is a single `/ingest` point which validates input as being properly formatted. There is strict typechecking and parametirized input into SQL commands such that SQL injection should not be a concern. There are other pages `/records` and `/check-buffer` to see the contents of the full record and buffer (of records), respectively. One can also check `/` to check basic availability. 

There are two databases in the system: `recordings` and `buffer_db`. `recordings` is the "master" database, the database intended to hold all records for long term analytics. `buffer_db` is, as the name indicates, a buffer database. It holds a number of records up to a defined threshold, at which point it will push all records it holds and flush itself. The purpose for this is to isolate the (more important) final database from every device recording by pushing to it in intervals instead on every call. 

Note that it is probably wise to perform some sort of mirroring of the `recordings` database. This could be done in a similar fashion to the built in buffer system between `buffer_db` and `recordings`, though likely it would be better to update and host a copy of `recordings` to an entirely independent system whenever checkpointing seems reasonable e.g. every six hours, every day, every 1,000 records, &c. 

Some simplifying assumptions made are the following:
    - All records submitted are unique in at least one field. This *seems* to be a safe assumption. The timestamp granularity is down to the second, and it *seems* unlikely that there would be more than one report generated in any given second. 

## Trade-Offs
The system has eventual consistency as outlined in **Design Decisions & Assumptions**. The reason for this is that typically, in the these systems hoping to do post hoc analytics there is simply little reason for immediate consistency. Instead it is better to isolate the interaction with the "master" database to be as infrequent as possible.

Admittedly, the system as currently implemented does not make many considerations for performace. It is an exceedingly simple, yet (hopefully) secure, implementation of the desired service. 

## Scalability Strategy
To address scalability, it is first important to consider if the entire service is being handled by multiple machines or a single machine. This is relevant as the solution space changes considerably

### Multiple Machines (Horizontal Scaling)
This case may be thought of crudely though accurately as throwing resources at the problem. If there were concerns of a single machine being overloaded with requests, simply providing more machines to handle the requese immediately reduce the load of the existing machines. 

Practically, how this could work is defining a mapping from sets of devices (those which produdce and report records) to particular machines, acting as the `POST/ingest` endpoints. To enable fault tolerance (of a machine endpoint), each of the devices should have knowledge of other machines which they may report their records to in the case of machine failure. This provides additional simple load balancing by its very nature. 

On the other side, each machine endpoint could then report their records to some master database. This could occur via cloud infrastructure e.g. S3/Lambda functions or another phsyical "master" endpoint. Though I would recommend the former. How the reporting occurs (e.g. stream or batch uploads) should be determined in accordance with the architecture chosen. For an S3/Lambda function, batching is more cost efficient due to mandatory memory mediums on AWS.

### Single Machine (Vertical Scaling)
If all records are being reported to a single machine, then there is more work to be done. 

If the machine were to become overburdened, this can lead to failed requests and retries, and eventual cascaded failures. A classic solution to this problem is to implement exponential backoff, where reporting machines delay subsequent reports exponentially on incurring repeated failures.  

## A Note about DoS
In a system like this, an immediate concern to security and availability would be denial of service (DoS) attacks. This could be mounted by an adversary by simply flooding reports to the endpoint with the intention of overloading it leading to service failure and preventing genuine reports from being processed. 

While this is a natural concern it is also easily mitigated. Permissioned access to the system via tokenization is an elegant solution. However, it is more likely that a permissioned network, one not accessible to users not on it, would also be both stronger and simpler. It is a typical solution within the manufacturing industry hoping to achieve the same architecture/goals. All that said, tokenization in conjunction with a permissioned network provides the stronest guarantees. 

## Observability
It seems to be that the system must meet and maintain a few properties: availability, integrity, confidentiality, and liveness. The systems availability may be monitored by simple pings and ensuring that the databases are updating (in this sense, just that they are growing is likely sufficient). The databases integrity must be monitored to ensure they have not been manipulated via malicious input or otherwise corrupted. Automated audits can address this. While this system should likely have permissioned access, implementing authentication tokens helps as well. Addressing confidentiality, it should not be possible to recover or otherwise induce the system from leaking its contents. To ensure that even if it *does* happen to leak contents, all data stored which may be accessible by outside networks should be encrypted using modern practices. As mentioned above this system should likely reside on a permissioned network, mitigating some of these concerns. In terms of liveness, the system should be able to handle record requests and respond to queries. Each device reporting to the service should have some system by which they make notifications when their records are not being processed. 

## LLM Usage Disclosure
There was some usage of ChatGPT which I tried to keep to a minumum. It was used primarily for skeleton code, error debugging, curl command generation, validation of some of my security ideas, and to generate github workflows. Every response was subject to critical manual review. The entire transcript may be found in the file LLMUsage.md. 