# Migrate Load Balancer Route53 records

I had to migrate all of a Route53 zone's records from an ELB to an ALB. However the zone wasn't terraformed.

Thus I made this script that allows to get all of a zone's records pointing to a LB, and updating the records one by one to another LB.

This is very specific use case, but I make it open-source in case someone find themselves in the same situation as me. 😌

The script can be easily adapted to update other types of records.

## Usage

The scripts uses [boto3](https://github.com/boto/boto3) to cummunicate with the AWS API.

```sh
$ pip3 install boto3
$ python3 migrate-lb-records-route53.py
usage: migrate-lb-records-route53.py [-h] --hosted-zone HOSTED_ZONE --old-lb
                                     OLD_LB --new-lb NEW_LB
                                     [--comment COMMENT]
migrate-lb-records-route53.py: error: the following arguments are required: --hosted-zone, --old-lb, --new-lb
```
