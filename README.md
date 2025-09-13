# README

readme things here

## Scalability Strategy
To address scalability, it is first important to consider if the entire service is being handled by multiple machines or a single machine. This is relevant as the solution space changes considerably

### Multiple Machines (Horizontal Scaling)
This case may be thought of crudely though accurately as throwing resources at the problem. If there were concerns of a single machine being overloaded with requests, simply providing more machines to handle the requese immediately reduce the load of the existing machines. 

Practically, how this could work is defining a mapping from sets of devices (those which produdce and report records) to particular machines, acting as the *POST/ingest* endpoints. To enable fault tolerance (of a machine endpoint), each of the devices should have knowledge of other machines which they may report their records to in the case of machine failure. This provides additional simple load balancing by its very nature. 

On the other side, each machine endpoint could then report their records to some master database. This could occur via cloud infrastructure e.g. S3/Lambda functions or another phsyical "master" endpoint. Though I would recommend the former. How the reporting occurs (e.g. stream or batch uploads) should be determined in accordance with the architecture chosen. For an S3/Lambda function, batching is more cost efficient due to mandatory memory mediums on AWS.

### Single Machine (Vertical Scaling)
If all records are being reported to a single machine, then there is more work to be done. 

If the machine were to become overburdened, this can lead to failed requests and retries, and eventual cascaded failers. A classic solution to this problem is to implement exponential backoff, where reporting machines delay subsequent reports exponentially on incurring consecutive failures.  

## A Note about DoS


## Observability

