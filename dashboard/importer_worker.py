import json

import boto.sns
import boto.sqs
from boto.sqs.message import Message
from django.conf import settings


def push_batch(queue, elems):
    conn = boto.sqs.connect_to_region(
        'us-east-1', # TODO: make this an env variable?
        aws_access_key_id=settings.SQS_ACCESS_ID,
        aws_access_secret_key=settings.SQS_ACCESS_ID)
    queue = conn.get_queue(settings.SQS_IMPORT_QUEUE)
    for e in elems:
        queue.write(e.as_message())

def trigger_start():
    conn = boto.sns.connect_to_region(
        'us-east-1', # TODO: make this an env variable?
        aws_access_key_id=settings.SQS_ACCESS_ID,
        aws_access_secret_key=settings.SQS_ACCESS_ID)
    conn.publish(settings.SNS_IMPORT_BUS, 'import_queue')


class Element(object):
    def __init__(self, type, payload):
        self.type = type
        self.payload = payload

    def as_blob(self):
        return json.dumps({
            'type': self.type,
            'payload': self.payload,
        })

    def as_message(self):
        m = Message()
        m.set_body(self.as_blob())
        return m
