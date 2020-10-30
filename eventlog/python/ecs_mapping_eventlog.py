# -*- coding: utf-8 -*-
"""Script for mapping an event log record to the Elastic Common Schema (ECS).

Example:
    Usage with NXLog using the `xm_json`_ and `xm_python`_ modules::

        nxlog.conf
        ~~~~~~~~~~~~
        <Extension _json>
            Module     xm_json
            DateFormat YYYY-MM-DD hh:mm:ss.sUTC
        </Extension>

        <Extension _python>
            Module     xm_python
            PythonCode modules/extension/python/py/ecs_mapping_eventlog.py
        </Extension>

        <Input eventlog>
            Module im_msvistalog

            ...

            <Exec>
                # Convert event record to a JSON formatted string and set $raw_event field using the result.
                to_json();

                # Call the process_json function from the Python script to process the event record. This will
                # update the JSON data stored in the $raw_event mapped to the Elastic Common Schema (ECS).
                python_call('process_json');
            </Exec>
        </Input>


.. _xm_json: https://nxlog.co/documentation/nxlog-user-guide/xm_json.html
.. _xm_python: https://nxlog.co/documentation/nxlog-user-guide/xm_python.html

"""

import json

# The field name used for retrieving the event record data.
EVENT_RECORD_FIELD_RAW_EVENT = 'raw_event'

# Global values used for mapping an event record to the Elastic Common Schema (ECS).
ECS_VERSION       = '1.0.4'
ECS_EVENT_DATASET = 'eventlog'
ECS_EVENT_KIND    = 'event'


def _pop(source, key, default=None):
    """Removes the provided key from the provided source and returns the corresponding value.

    :param source: the source dictionary
    :param key: the value key
    :param default: the default value to return
    :return: the provided default if the source is not provided or does not contain the specified key

    """
    value = default
    if source:
        if key in source:
            value = source.pop(key)
        elif key.casefold() in source:
            value = source.pop(key.casefold())
    return value


def _compact(source):
    """Returns a new dictionary containing only those key/value pairs that equate to None, including nested values.

    :param source: the source dictionary
    :return: a new dictionary with all key/value pairs that equate to None removed or None if the operations results in
    dictionary with no values

    """
    c = {}
    for k, v in source.items():
        if isinstance(v, dict):
            v = _compact(v)
        if v is not None:
            c[k] = v
    return c or None


def map_to_ecs(event_record):
    """Maps the fields from the provided dictionary representing an event record to the Elastic Common Schema (ECS)
    and returns a new dictionary containing the result.

    :param event_record: dictionary representing an event record
    :return: a new dictionary containing key/value pairs from the event record mapped to ECS

    """
    if not event_record:
        return None

    # ECS : root
    # ========================================
    ecs = {
        'version': ECS_VERSION,
    }

    # ECS : destination
    # ========================================
    destination = {
        'address': _pop(event_record, 'DestinationHostname'),
        'ip': _pop(event_record, 'DestinationIp'),
        'port': _pop(event_record, 'DestinationPort')
    }

    ecs['destination'] = destination

    # ECS : event
    # ========================================
    event = {
        'category': _pop(event_record, 'Category'),
        'code': _pop(event_record, 'EventID'),
        'created': _pop(event_record, 'EventReceivedTime'),
        'dataset': ECS_EVENT_DATASET,
        'end': _pop(event_record, 'EventTime'),
        'kind': ECS_EVENT_KIND,
        'module': _pop(event_record, 'SourceModuleName'),
        'provider': _pop(event_record, 'SourceName'),
        'sequence': _pop(event_record, 'RecordNumber'),
        'severity': _pop(event_record, 'SeverityValue'),
        'start': _pop(event_record, 'EventTime'),
        'type': _pop(event_record, 'EventType')
    }

    ecs['event'] = event

    # ECS : file
    # ========================================
    file_hashes = {}

    if 'Hashes' in event_record:
        hashes = _pop(event_record, 'Hashes').strip().split(',')
        file_hashes = {p[0]: p[1] for p in [s.split('=') for s in hashes] if len(p) == 2}

    file = {
        'hash': file_hashes,
        'path': _pop(event_record, 'Image')
    }

    ecs['file'] = file

    # ECS : host
    # ========================================
    host = {
        'hostname': _pop(event_record, 'Hostname'),
        'name': _pop(event_record, 'FQDN')
    }

    ecs['host'] = host

    # ECS : log
    # ========================================
    log = {
        'level': _pop(event_record, 'Severity')
    }

    ecs['log'] = log

    # ECS : message
    # ========================================
    ecs['message'] = _pop(event_record, 'Message')

    # ECS : process
    # ========================================
    process = {
        'pid': _pop(event_record, 'ExecutionProcessID'),
        'thread': {
            'id': _pop(event_record, 'ExecutionThreadID')
        }
    }

    ecs['process'] = process

    # ECS : source
    # ========================================
    source = {
        'address': _pop(event_record, 'SourceHostname'),
        'ip': _pop(event_record, 'SourceIp'),
        'port': _pop(event_record, 'SourcePort')
    }

    ecs['source'] = source

    # ECS : tags
    # ========================================
    ecs['tags'] = None

    # ECS : user
    # ========================================
    user = {
        'domain': _pop(event_record, 'Domain'),
        'id': _pop(event_record, 'UserID')
    }

    ecs['user'] = user

    # ECS : event_data
    # ========================================
    ecs['event_data'] = event_record

    return _compact(ecs)


def process_json(event):
    """Process the raw JSON data for an event record.

    :param event: the event record containing the raw JSON data for an event.

    """
    # TODO: Currently only handles event records produced by NXLog. Should be expanded to handle other sources.
    if event.get_field(EVENT_RECORD_FIELD_RAW_EVENT):
        event_record_json = json.loads(event.get_field(EVENT_RECORD_FIELD_RAW_EVENT))
        event.set_field(EVENT_RECORD_FIELD_RAW_EVENT, json.dumps(map_to_ecs(event_record_json)))
