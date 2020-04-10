import os
import unittest

from unittest.mock import Mock

import ecs_mapping_eventlog


def get_field(name):
    if name == ecs_mapping_eventlog.EVENT_RECORD_FIELD_RAW_EVENT:
        with open(os.path.join(os.path.dirname(__file__), 'test_event_record.json'), 'rb') as f:
            return f.read()
    return None


def set_field(name, value):
    print(f'Setting field {name} with value:\n{value}\n')


nxLogData = Mock()
nxLogData.get_field = get_field
nxLogData.set_field = set_field


class EcsMappingEventlogTest(unittest.TestCase):
    def test_process_event_nxlog(self):
        ecs_mapping_eventlog.process_json(nxLogData)


if __name__ == '__main__':
    unittest.main()
