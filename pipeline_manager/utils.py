import re, datetime, pytz, sys
from functools import cache


p = re.compile(r"(\d+)(d|h|m|s|ms)")
def human_time(time_string : str):
    """Returns a timedelta from a human readible string, e.g., "5h 3m"."""
    t = {}
    for c in time_string.split(' '):
        m = p.match(c)
        if m is not None:
            t[m.group(2)] = int(m.group(1))
    return datetime.timedelta(days=t.get('d', 0), hours=t.get('h', 0), minutes=t.get('m', 0), seconds=t.get('s', 0), microseconds=t.get('ms', 0)).total_seconds()

def get_callable(f):
    if callable(f):
        return f
    else:
        chunks = f.split(".")
        o = globals()[chunks.pop(0)]
        while chunks:
            o = getattr(o, chunks.pop(0))
        return o

def merge_intervals(intervals):
    if intervals:
        sort = sorted(list(intervals))
        i = 0
        merged = []
        current = sort.pop(0)
        while sort:
            nxt = sort.pop(0)
            if nxt[0] <= current[1]:
                current = (current[0], max(current[1], nxt[1]))
            elif nxt[0] > current[1]:
                merged.append(current)
                current = nxt
        merged.append(current)
        return merged
    else:
        return []


def f_timestamp(timestamp : int):
    return pytz.utc.localize(datetime.datetime.utcfromtimestamp(timestamp)).strftime('%Y-%m-%dT%H:%M:%S%z')

def align_start_time(start_time, window, offset=0):
    if ((start_time - offset) % window == 0):
        return start_time
    else:
        return offset + ((start_time - offset) // window + 1) * window

def align_end_time(end_time, window, offset=0):
    return offset + ((end_time - offset) // window) * window
    
@cache
def get_profile():
    from .data_handler import DataHandler

    try:
        f = None
        raise Exception
    except:
        frame = sys.exc_info()[2].tb_frame
        f = frame
    finally:
        while f:
            if isinstance(f.f_locals.get('self', None), DataHandler):
                return f.f_locals['self'].profile
            f = f.f_back
        return None

def profile_lookup(key, *args):

    if args:
        default = True
        default_value = args[0]
    else:
        default = False
    
    target = get_profile()
    try:
        for t in key.split('.'):
            target = target[t]
    except KeyError as e:
        if default:
            target = default_value
        else:
            raise e
    return target