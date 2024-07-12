import re
import time

"""
Duration and distance
"""

def calculate_duration(text):
    # get second
    if "sec" in text:
        second = text.split()[0]
        return int(second)/60
    duration_pattern = r"((\d+)\shr)?\s?((\d+)\smin)?"
    m = re.match(duration_pattern, text)
    hour = m.group(2)
    minute = m.group(4)

    hour = int(hour) if isinstance(hour, str) else 0
    minute = int(minute) if isinstance(minute, str) else 0

    return hour * 60 + minute

def read_duration(text):
    if "sec" in text:
        second = text.split()[0]
        res = second + " second"
        if int(second) != 1:
            res += 's'
        return res
    duration_pattern = r"((\d+)\shr)?\s?((\d+)\smin)?"
    m = re.match(duration_pattern, text)
    hour = m.group(2)
    minute = m.group(4)

    result = ""

    if isinstance(hour, str):
        result += hour + " hour"
        if int(hour) != 1:
            result += 's'
        if isinstance(minute, str):
            result += " and " + minute + " minute"
            if int(minute) != 1:
                result += 's'
    elif isinstance(minute, str):
        result += minute + " minute"
        if int(minute) != 1:
                result += 's'

    return result

def calculate_distance(text):
    distance_pattern = r"(\d+)(\.(\d+))?\s(k)?m"
    m = re.match(distance_pattern, text)
    if m.group(4): #kilometer
        if m.group(3):
            value = float(m.group(1) + '.' + m.group(3)) * 1000
        else:
            value = float(m.group(1)) * 1000
    else:
        value = float(m.group(1))
    return value

def read_distance(text):
    distance_pattern = r"(\d+)(\.(\d+))?\s(k)?m"
    m = re.match(distance_pattern, text)
    res = m.group(1)
    value = None
    if m.group(3):
        res += " point " + m.group(3)
    value = res
    res += ' '
    if m.group(4): #kilometer
        res += "kilo"
    res += "meter"
    if float(value.replace(" point ", '.')) != 1:
        res += 's'
    return res

"""
Loop function
"""

def loop_function(func, *args, max_loop=10, wait_time=0.3, length_non_zero=False, **kwargs):
    exception = Exception
    for i in range(max_loop):
        try:
            res = func(*args, **kwargs)
            if length_non_zero and isinstance(res, list):
                if len(res) == 0:
                    raise ValueError
            return res
        except Exception as e:
            exception = e
        time.sleep(wait_time)
    raise exception

"""
Make direction speech
"""

def create_direction_speech(origin, destination, total_distance, total_duration, direction_dict):
    res = [f"These are the directions from {origin} to {destination} with the estimated time {read_duration(total_duration)} and overall distance of {read_distance(total_distance)}:"]
    step_count = 1
    for k, v in direction_dict.items():
        parent_text, parent_time_distance = k

        parent_time, parent_distance = parent_time_distance.split("(")
        parent_time = parent_time.strip()
        parent_distance = parent_distance.replace(')','')

        if len(v) == 0:
            res.append(
                f"Step {step_count} , {parent_text} , go forward for {read_distance(parent_distance)}"
            )
            step_count += 1
        else:
            for el in v:
                res.append(
                    f"Step {step_count} , {el[0]} , go forward for {read_distance(el[1])}"
                )
                step_count += 1
    res.append(
        "At this point, you have arrived at the destination"
    )
    return '\n'.join(res)