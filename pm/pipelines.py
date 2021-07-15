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

    'activity_demo': {
        'description': "Demo pipeline used for activity coaching.",
        'recurrence': '1m',
        'models': {
            'situation': [
                {
                    'name': 'activity_demo_situation_stationary',
                    'inputs': [
                        'feat_active_seconds',
                    ],
                    'output': 'situ_demo_situation_stationary'
                }
            ],
            'coaching': {
                'name': 'activity_demo_coaching',
                'inputs': [],
                'output': 'coach_demo_situation_stationary'
            },
            'rendering': {
                'name': 'activity_demo_rendering',
                'inputs': [],
                'output': 'rendr_demo_situation_stationary'
            },
        }
    },

    'sleep_quality': {
        'description': "Pipeline for the coaching of sleeping quality.",
        'recurrence': {'period': '24h', 'offset': '12h'},
        'models': {
            'situation': [], # No models, situation assessment is calculated as features
            'coaching': {
                'name': 'sleep_coaching',
                'inputs': [
                    'situ_sleep_subjective_quality_qualitative_weekly', # from sleep diary, default value = 1
                    'situ_sleep_latency_qualitative_weekly', # from situation model
                    'situ_sleep_napped_during_day_weekly', # calculated, 0 = False, 1 = True, default value = 0
                    'situ_sleep_efficiency_qualitative_weekly', # from situation model
                    'situ_sleep_disturbance_type_weekly', # calculated (fusion of features and diary), values: medical, temperature, bathroom, none; default value = none
                    'situ_activity_physical_weekly', # from situation model, from activity pipeline
                ],
                'output': 'coach_sleep_quality'
            },
            'rendering': {}
        },
        'parameters': [
            'situ_sleep_overall_sleep_quality',
            'situ_sleep_maximum_sleep_quality',
            'fuse_sleep_latency',
            'situ_sleep_napped_minutes',
            'situ_sleep_awake_minutes',
            'feat_sleep_temperature',
            'situ_sleep_number_disturbances',
            'situ_sleep_coaching_reliability_weekly' # reliability of coaching action
        ]
    },

    'activity_cooking': {
        'description': "Pipeline for the coaching of cooking activity.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_activity_cooking',
                    'inputs': [
                        'feat_cooking_recorded',
                        'feat_cooking_predicted'
                    ],
                    'output': 'situ_activity_cooking'
                }
            ],
            'coaching': {
                'name': 'coach_activity_cooking',
                'inputs': [
                    'situ_activity_cooking',
                ],
                'output': 'coach_activity_cooking'
            },
            'rendering': {}
        },
        'parameters': [
            'feat_activity_cooking_weekly_average'
        ]
    },

    'activity_outside': {
        'description': "Pipeline for the coaching of general outside activity.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_activity_outside',
                    'inputs': [
                        'feat_activity_outside_recorded',
                        'feat_activity_outside_predicted',
                    ],
                    'output': 'situ_activity_outside'
                }
            ],
            'coaching': {
                'name': 'coach_activity_outside',
                'inputs': [
                    'situ_activity_outside',
                ],
                'output': 'coach_activity_outside'
            },
            'rendering': {}
        },
        'parameters': [
            'feat_outside_time_weekly'
        ]
    },

    'social_friends': {
        'description': "Pipeline for the coaching of social activity with friends.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_social_activity_friends',
                    'inputs': [
                        'feat_calls_count_friends_relative', # relative over "all" available data (or  2 months)
                        'feat_calls_duration_friends_relative', # --||--
                        'feat_visits_friends_relative_past_week', # relative over the past week
                        'feat_visits_friends_relative', #relative over "all" data
                        'feat_outside_friends_relative_past_week',
                        'feat_outside_friends_relative',
                        'feat_calls_count_friends_weekly_vs_goal',
                        'feat_visits_count_friends_weekly_vs_goal',
                        'feat_outside_count_friends_weekly_vs_goal',
                    ],
                    'output': 'situ_social_activity_friends'
                }
            ],
            'coaching': {
                'name': 'coach_social_activity_friends',
                'inputs': [
                    'situ_social_activity_friends',
                    'feat_social_activity_friends_qualitative_lowest',
                    'profile_social_invite_possible_friends',
                    'profile_social_interaction_preferrence'
                ],
                'output': 'coach_social_activity_friends'
            },
            'rendering': {}
        }
    },

    'social_family': {
        'description': "Pipeline for the coaching of social activity with family.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_social_activity_family',
                    'inputs': [
                        'feat_calls_count_family_relative', # relative over "all" available data (or  2 months)
                        'feat_calls_duration_family_relative', # --||--
                        'feat_visits_family_relative_past_week', # relative over the past week
                        'feat_visits_family_relative', #relative over "all" data
                        'feat_outside_family_relative_past_week',
                        'feat_outside_family_relative',
                        'feat_calls_count_family_weekly_vs_goal',
                        'feat_visits_count_family_weekly_vs_goal',
                        'feat_outside_count_family_weekly_vs_goal',
                    ],
                    'output': 'situ_social_activity_family'
                }
            ],
            'coaching': {
                'name': 'coach_social_activity_family',
                'inputs': [
                    'situ_social_activity_family',
                    'feat_social_activity_family_qualitative_lowest',
                    'profile_social_invite_possible_family',
                    'profile_social_interaction_preferrence'
                ],
                'output': 'coach_social_activity_family'
            },
            'rendering': {}
        }
    },

    'social_general': {
        'description': "Pipeline for the coaching of general social activity.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_social_activity_general',
                    'inputs': [
                        'feat_calls_count_total_relative', # relative over "all" available data (or 2 months)
                        'feat_calls_duration_total_relative', # --||--
                        'feat_visits_total_relative_past_week', # relative over the past week
                        'feat_visits_total_relative', #relative over "all" data
                        'feat_outside_total_relative_past_week',
                        'feat_outside_total_relative',
                        'feat_calls_count_total_weekly_vs_goal',
                        'feat_visits_count_total_weekly_vs_goal',
                        'feat_outside_count_total_weekly_vs_goal',
                    ],
                    'output': 'situ_social_activity_general'
                }
            ],
            'coaching': {
                'name': 'coach_social_activity_general',
                'inputs': [
                    'situ_social_activity_general',
                    'feat_social_activity_total_qualitative_lowest',
                    'profile_social_invite_possible_general',
                    'profile_social_interaction_preferrence'
                ],
                'output': 'coach_social_activity_general'
            },
            'rendering': {},
            'parameters': [
                'av_time_outside_minutes_prev7days'
            ]
        }
    },

    'social_community': {
        'description': "Pipeline for the coaching of community involvement.",
        'recurrence': '24h',
        'models': {
            'situation': [
                {
                    'name': 'situ_social_activity_community',
                    'inputs': [
                        'feat_community_habitual_relative', # relative over "all" available data (or 2 months)
                        'feat_community_habitual_weekly_vs_goal',
                        'feat_community_nonhabitual',
                    ],
                    'output': 'situ_social_activity_community'
                }
            ],
            'coaching': {
                'name': 'coach_social_activity_community',
                'inputs': [
                    'situ_social_activity_community',
                    'profile_social_planned_event_available',
                    'profile_social_invite_possible_general',
                    'profile_social_interaction_preferrence'
                ],
                'output': 'coach_social_activity_community'
            },
            'rendering': {}
        }
    },

    'mobility_general_stand_up': {
        'description': 'Pipeline for the coaching of ability to stand up.',
        'recurrence': '1d',
        'models': {
            'situation': [
                {
                    'name': 'situ_mobility_stand_up',
                    'inputs': [
                        'feat_mobility_stand_up_count',
                        'feat_mobility_stand_up_mode',
                        'feat_mobility_stand_up_time'
                    ],
                    'output': 'situ_mobility_stand_up'
                }
            ],
            'coaching': {
                'name': 'coach_mobility_stand_up',
                'inputs': [
                    'situ_mobility_stand_up',
                    'situ_mobility_stand_up_predicted'
                ],
                'output': 'coach_mobility_stand_up'
            },
            'rendering': {},
        },
        'parameters': [
            'feat_mobility_stand_up_count_weekly'
        ]

    },

    'mobility_general_stand': {
        'description': 'Pipeline for the coaching of ability to stand.',
        'recurrence': '1d',
        'models': {
            'situation': [
                {
                    'name': 'situ_mobility_standing',
                    'inputs': [
                        'feat_mobility_standing_episode_length',
                        'feat_mobility_standing_daily_duration',
                        'feat_mobility_standing_mode'
                    ],
                    'output': 'situ_mobility_standing'
                }
            ],
            'coaching': {
                'name': 'coach_mobility_standing',
                'inputs': [
                    'situ_mobility_standing',
                    'situ_mobility_standing_predicted'
                ],
                'output': 'coach_mobility_standing'
            },
            'rendering': {},
        },
        'parameters': [
            'feat_mobility_standing_duration_weekly'
        ]
    },

    'mobility_general_walk': {
        'description': 'Pipeline for the coaching of ability to walk.',
        'recurrence': '1d',
        'models': {
            'situation': [
                {
                    'name': 'situ_mobility_walking',
                    'inputs': [
                        'feat_mobility_walking_episode_distance_qualitative',
                        'feat_mobility_walking_daily_distance_qualitative',
                        'feat_mobility_walking_duration_qualitative',
                        'feat_mobility_walking_mode',
                        'feat_mobility_walking_instabilities_count',
                        'feat_mobility_walking_falls_count',
                    ],
                    'output': 'situ_mobility_walking'
                }
            ],
            'coaching': {
                'name': 'coach_mobility_walking',
                'inputs': [
                    'situ_mobility_walking',
                    'situ_mobility_walking_predicted'
                ],
                'output': 'coach_mobility_walking'
            },
            'rendering': {},
        },
        'parameters': [
            'feat_mobility_walking_step_count_weekly',
            'feat_mobility_walking_distance_weekly'
        ]

    },

    'mobility_general_stairs': {
        'description': 'Pipeline for the coaching of ability to use stairs.',
        'recurrence': '1d',
        'models': {
            'situation': [
                {
                    'name': 'situ_mobility_use_stairs',
                    'inputs': [
                        'feat_mobility_use_stairs_count',
                        'feat_mobility_use_stairs_mode',
                        'feat_mobility_use_stairs_time_per',
                        'feat_mobility_use_stairs_rest_count',
                        'feat_mobility_use_stairs_rest_duration',
                    ],
                    'output': 'situ_mobility_use_stairs'
                }
            ],
            'coaching': {
                'name': 'coach_mobility_use_stairs',
                'inputs': [
                    'situ_mobility_use_stairs',
                    'situ_mobility_use_stairs_predicted'
                ],
                'output': 'coach_mobility_use_stairs'
            },
            'rendering': {},
        },
        'parameters': [
            'feat_mobility_use_stairs_count_weekly'
        ]
    },

    'mobility_instructed_walking': {
        'description': 'Pipeline for the coaching of instructed walking mobility.',
        'recurrence': '4h',
        'models': {
            'situation': [
                {
                    'name': 'situ_mobility_instructed_walking',
                    'inputs': [
                        'feat_walking_longest_episode_exceeded',
                        'feat_walking_time_threshold_reached',
                    ],
                    'output': 'situ_mobility_instructed_walking',
                }
            ],
            'coaching': {
                'name': 'coach_mobility_instructed_walking',
                'inputs': [
                    'situ_mobility_instructed_walking',
                ],
                'output': 'coach_mobility_instructed_walking'
            },
            'rendering': {},
        },
        'parameters': [
            'feat_walking_time_cumulative',
            'feat_walking_longest_episode_length'
        ]
    },    
}
