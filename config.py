"""
Regex configuration for checkhealth.

The top–level keys are the log levels that appear in the square brackets
at the start of a line; the next two levels are the thread and class
names.  Values are lists of `(name, pattern, comment)` tuples, where
comment is optional (defaults to empty string).
"""

CONFIGURED_REGEXES = {
    'ERROR': {
        'Plugin': {
            'data.OmniDataImpl': [
                ('omni_availability_file', r'Availability: Loaded 0 lines from csv', 'Indicates no data loaded from CSV'),
            ],
        },
    },
    'WARN': {
        'ker-15': {
            'dapter.SolaceLocateMessageFilter': [
                ('locate_instrument_resolution', r'Failed to resolve .*', 'Instrument resolution failure'),
            ],
        },
    },
}