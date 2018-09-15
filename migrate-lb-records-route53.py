#!/usr/bin/env python3

import argparse
import re
import boto3

# Define accepted arguments
parser = argparse.ArgumentParser()
parser.add_argument('--hosted-zone',
                    dest='hosted_zone',
                    required=True),
parser.add_argument('--old-lb',
                    dest='old_lb',
                    required=True),
parser.add_argument('--new-lb',
                    dest='new_lb',
                    required=True),
parser.add_argument('--comment',
                    dest='comment',
                    required=False),
args = parser.parse_args()

if not args.comment:
    # Comment is mendatory, set it to an empty string if not set by the user
    args.comment = ''

# Verify LB hostnames
assert re.match(r'^[a-zA-Z0-9\-]+\.[a-z]+\-[a-z]+\-[0-9].elb\.amazonaws\.com$',
                args.old_lb), ('Old LB "' + args.old_lb + '" does not seem to be a valid AWS LB hostname')
assert re.match(r'^[a-zA-Z0-9\-]+\.[a-z]+\-[a-z]+\-[0-9].elb\.amazonaws\.com$',
                args.new_lb), ('New LB "' + args.new_lb + '" does not seem to be a valid AWS LB hostname')

# Convert LB hostnames to DNS entries
args.old_lb = args.old_lb + '.'
args.new_lb = args.new_lb + '.'

# Create an empty list that will contain names of the old LB records
records_to_update = list()


def get_zone(next_record_name):
    if next_record_name != '':
        return boto3.client('route53').list_resource_record_sets(HostedZoneId=f'{args.hosted_zone}', StartRecordName=f'{next_record_name}')
    else:
        return boto3.client('route53').list_resource_record_sets(HostedZoneId=f'{args.hosted_zone}')


def get_records(zone):
    # Append all the old LB records names to the list
    for record in zone['ResourceRecordSets']:
        if record['Type'] == "CNAME":
            if record['ResourceRecords'][0]['Value'] == args.old_lb:
                records_to_update.append(record['Name'])


def get_whole_zone(zone):
    # The API can only return 100 records at a time. If there is more,
    # the response will have a 'NextRecordName' and we will be able
    # to get all the next records starting 'NextRecordName'.
    if 'NextRecordName' in zone:
        next_record_name = zone['NextRecordName']
        zone = get_zone(next_record_name)
        get_records(zone)
        # The function calls itself until we have gone trough the whole zone
        get_whole_zone(zone)


# First we get the zone without a 'NextRecordName'
zone = get_zone('')
get_records(zone)
get_whole_zone(zone)

print("\nRecords to update:\n\n" + str(records_to_update))

# Update each record one by one
for record_name in records_to_update:
    # Ask confirmation to the user
    msg = '\nDo you really want to update %s?' % record_name[:-1]
    update = input("%s (y/N) " % msg).lower() == 'y'

    if update:
        # Create the change_batch dict
        change_batch = {
            "Comment": args.comment,
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                        "Name": record_name,
                        "Type": "CNAME",
                        "TTL": 600,
                        "ResourceRecords": [{
                            "Value": args.new_lb
                        }]
                        }
            }]
        }

        print("\nUpdating zone with the following records:\n\n" + str(change_batch))

        msg = '\nDo you really want to update ?'
        update = input("%s (y/N) " % msg).lower() == 'y'

        # Actually update the record using the API
        response = boto3.client('route53').change_resource_record_sets(
            HostedZoneId=args.hosted_zone,
            ChangeBatch=change_batch
        )

        print("\nboto3.client('route53').change_resource_record_set returned response:\n\n" + str(response))

print("\nWARNING: Response normally contains a 'Status' entry, and the value is normally 'PENDING'. That means you need to wait a bit (5 min) before the record get actually updated. ")
