import re
import sys
from collections import defaultdict

# Configured regexes segregated into sections, further by thread and class
CONFIGURED_REGEXES = {
    'ERROR': {
        'Plugin': {
            'data.OmniDataImpl               ': [
                ('omni_availability_file', r'Availability: Loaded 0 lines from csv')
            ]
        },
        # Example: 'some-thread': {
        #     'some-class': [('error_type', r'regex_pattern')]
        # }
    },
    'WARN': {
        'ker-15': {
            'dapter.SolaceLocateMessageFilter': [
                ('locate_instrument_resolution', r'Failed to resolve .*')
            ]
        },
        # Add more threads and classes as needed
    },
    # Add other levels if needed
}

# Regex to parse line structure: [level] [thread][class]
LINE_PARSER = re.compile(r'\[(\w+)\]\s*\[([^\]]+)\]\[([^\]]+)\]')

def classify_lines(input_stream):
    matched_counts = defaultdict(int)  # (thread, class_name) -> count
    unmatched_counts = {}  # (thread, class_name) -> {'count': int, 'sample': str}
    
    for line in input_stream:
        line = line.strip()
        match = LINE_PARSER.search(line)
        if match:
            level, thread, class_name = match.groups()
            if level in CONFIGURED_REGEXES and thread in CONFIGURED_REGEXES[level] and class_name in CONFIGURED_REGEXES[level][thread]:
                matched = False
                for name, pattern in CONFIGURED_REGEXES[level][thread][class_name]:
                    if re.search(pattern, line):
                        matched_counts[(thread, class_name)] += 1
                        matched = True
                        break  # First match wins
                if not matched:
                    key = (thread, class_name)
                    if key not in unmatched_counts:
                        unmatched_counts[key] = {'count': 0, 'sample': line}
                    unmatched_counts[key]['count'] += 1
            else:
                key = (thread, class_name)
                if key not in unmatched_counts:
                    unmatched_counts[key] = {'count': 0, 'sample': line}
                unmatched_counts[key]['count'] += 1
        else:
            key = ('unknown', 'unknown')
            if key not in unmatched_counts:
                unmatched_counts[key] = {'count': 0, 'sample': line}
            unmatched_counts[key]['count'] += 1
    return matched_counts, unmatched_counts

def main():
    matched_counts, unmatched_counts = classify_lines(sys.stdin)
    
    print("Matched:")
    print("Thread".ljust(15) + " | " + "Class Name".ljust(50) + " | " + "Count".ljust(5))
    for (thread, class_name), count in matched_counts.items():
        print(f"{thread:<15} | {class_name:<50} | {count:<5}")
    
    print("\nUnmatched:")
    print("Thread".ljust(15) + " | " + "Class Name".ljust(50) + " | " + "Count".ljust(5) + " | " + "Sample Line")
    for (thread, class_name), data in unmatched_counts.items():
        print(f"{thread:<15} | {class_name:<50} | {data['count']:<5} | {data['sample']}")

if __name__ == "__main__":
    main()