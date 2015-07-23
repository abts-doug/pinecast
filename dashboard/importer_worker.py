import json

import boto.sns
from django.conf import settings


def push_batch(bus, payloads):
    conn = boto.sns.connect_to_region(
        'us-east-1', # TODO: make this an env variable?
        aws_access_key_id=settings.SQS_ACCESS_ID,
        aws_secret_access_key=settings.SQS_ACCESS_ID)
    for p in payloads:
        conn.publish(bus, json.dumps(p))
