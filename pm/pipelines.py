PIPELINES = {
    'system_test': {
        'description': "Initial pipeline used for testing.",
        'recurrence': {'period': '3m', 'offset': '0h'},
        'models': {
            'situation': [
                {
                    'name': 'system_test_situation_temperature',
                    'inputs': [
                        ('feat_system_test_temp_avg_5m', '3m'),
                    ],
                    'output': 'situ_system_test_temperature'
                }
            ],
            'coaching': {
                'name': 'system_test_coaching_temperature',
                'inputs': [
                    ('situ_system_test_temperature', '3m'),
                    ('feat_system_test_sleep_quality_5m', '3m')
                ],
                'output': 'coach_system_test_temperature'
            },
            'rendering': {
                'name': 'system_test_rendering_temperature',
                'inputs': [
                    ('coach_system_test_temperature', '3m')
                ],
                'output': 'rendr_system_test_temperature'
            }
        }
    }, 
}
