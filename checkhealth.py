import re
import sys
from collections import defaultdict

from config import CONFIGURED_REGEXES   # <-- pull in external configuration

# match anything between each pair of brackets; spaces removed later
LINE_PARSER = re.compile(r'\[([^\]]+)\]\s*\[([^\]]+)\]\[([^\]]+)\]')

# extract date and time at start of a line
TIMESTAMP_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{3})')

def _trim_after_last_bracket(line: str) -> str:
    """Return the portion of *line* after the last closing bracket,
    stripped of leading colon/whitespace."""
    idx = line.rfind(']')
    if idx != -1:
        msg = line[idx + 1 :].strip()
        if msg.startswith(':'):
            msg = msg[1:].strip()
        return msg
    return line.strip()

def classify_lines(input_stream):
    matched_counts = {}  # (level, thread, class_name, name) -> {'count': int, 'comment': str}
    unmatched_counts = {}  # (level, thread, class_name) -> {'count': int, 'first_time': str, 'first_sample': str, 'last_time': str, 'last_sample': str}

    for line in input_stream:
        line = line.rstrip('\n')
        # pull timestamp time portion (ignore date)
        ts_match = TIMESTAMP_RE.match(line)
        time = ts_match.group(2) if ts_match else ''

        match = LINE_PARSER.search(line)
        if match:
            level, thread, class_name = (s.strip() for s in match.groups())
            if (
                level in CONFIGURED_REGEXES
                and thread in CONFIGURED_REGEXES[level]
                and class_name in CONFIGURED_REGEXES[level][thread]
            ):
                matched = False
                for item in CONFIGURED_REGEXES[level][thread][class_name]:
                    name, pattern = item[0], item[1]
                    comment = item[2] if len(item) > 2 else ''
                    if re.search(pattern, line):
                        key = (level, thread, class_name, name)
                        if key not in matched_counts:
                            matched_counts[key] = {'count': 0, 'comment': comment}
                        matched_counts[key]['count'] += 1
                        matched = True
                        break
                if not matched:
                    key = (level, thread, class_name)
                    sample = _trim_after_last_bracket(line)
                    if key not in unmatched_counts:
                        unmatched_counts[key] = {
                            'count': 0,
                            'first_time': time,
                            'first_sample': sample,
                            'last_time': time,
                            'last_sample': sample,
                        }
                    unmatched_counts[key]['count'] += 1
                    unmatched_counts[key]['last_time'] = time
                    unmatched_counts[key]['last_sample'] = sample
            else:
                key = (level, thread, class_name)
                sample = _trim_after_last_bracket(line)
                if key not in unmatched_counts:
                    unmatched_counts[key] = {
                        'count': 0,
                        'first_time': time,
                        'first_sample': sample,
                        'last_time': time,
                        'last_sample': sample,
                    }
                unmatched_counts[key]['count'] += 1
                unmatched_counts[key]['last_time'] = time
                unmatched_counts[key]['last_sample'] = sample
        else:
            level = 'unknown'
            key = (level, 'unknown', 'unknown')
            sample = _trim_after_last_bracket(line)
            if key not in unmatched_counts:
                unmatched_counts[key] = {
                    'count': 0,
                    'first_time': time,
                    'first_sample': sample,
                    'last_time': time,
                    'last_sample': sample,
                }
            unmatched_counts[key]['count'] += 1
            unmatched_counts[key]['last_time'] = time
            unmatched_counts[key]['last_sample'] = sample

    return matched_counts, unmatched_counts

def main():
    level_filter = 'WARN'  # default
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ('WARN', 'ERROR'):
            level_filter = arg
        else:
            print("Usage: python checkhealth.py [WARN|ERROR]")
            sys.exit(1)

    matched_counts, unmatched_counts = classify_lines(sys.stdin)

    # Filter based on level_filter
    if level_filter == 'ERROR':
        filtered_matched = {k: v for k, v in matched_counts.items() if k[0] == 'ERROR'}
        filtered_unmatched = {k: v for k, v in unmatched_counts.items() if k[0] == 'ERROR'}
    else:  # WARN, show both WARN and ERROR
        filtered_matched = {k: v for k, v in matched_counts.items() if k[0] in ('WARN', 'ERROR')}
        filtered_unmatched = {k: v for k, v in unmatched_counts.items() if k[0] in ('WARN', 'ERROR')}

    total_matched = sum(data['count'] for data in filtered_matched.values())
    total_unmatched = sum(data['count'] for data in filtered_unmatched.values())

    if filtered_matched:
        print(f"Matched ({total_matched}):")
        print("Level".ljust(8) + " | " + "Thread".ljust(15) + " | " + "Class Name".ljust(50) + " | " + "Name".ljust(30) + " | " + "Count".ljust(5) + " | " + "Comment")
        for (level, thread, class_name, name), data in filtered_matched.items():
            print(f"{level:<8} | {thread:<15} | {class_name:<50} | {name:<30} | {data['count']:<5} | {data['comment']}")

    if filtered_unmatched:
        if filtered_matched:
            print()  # Add a blank line if both sections are present
        print(f"Unmatched ({total_unmatched}):")
        print(
            "Level".ljust(8)
            + " | "
            + "Thread".ljust(15)
            + " | "
            + "Class Name".ljust(50)
            + " | "
            + "Count".ljust(5)
            + " | "
            + "Order".ljust(5)
            + " | "
            + "Time".ljust(12)
            + " | Sample Line"
        )
        for (level, thread, class_name), data in filtered_unmatched.items():
            # first occurrence
            print(
                f"{level:<8} | {thread:<15} | {class_name:<50} | {data['count']:<5} | first |"
                f" {data['first_time']:<12} | {data['first_sample']}"
            )
            # last occurrence
            print(
                f"{level:<8} | {thread:<15} | {class_name:<50} | {data['count']:<5} | last  |"
                f" {data['last_time']:<12} | {data['last_sample']}"
            )

if __name__ == "__main__":
    main()