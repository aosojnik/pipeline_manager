from ...utils import human_time, profile_lookup
from datetime import datetime
import pytz


from itertools import groupby

def average(timestamp, timestep, inputs):
    if len(inputs) == 1:
        vals = [x[2] for x in next(iter(inputs.values()))]
        if vals:
            return [(timestamp, timestep, sum(vals) / len(vals))]
        else:
            # empty average is 0 by convention
            return [(timestamp, timestep, 0)]
    else:
        pass

def constant(value):
    def const(timestamp, timestep, *args, **kwargs):
        return [(timestamp, timestep, value)]
    return const

def extract_component(component):
    def extract(timestamp, timestep, inputs):
        vals = next(iter(inputs.values()))
        ret = [(val[0], val[1], list(val[2])[component]) for val in vals]
        return ret
    return extract

def alias(timestamp, timestep, inputs):
    return inputs

# Lag should only ever be used on calculated features, as these use fixed time timesteps.
# DO NOT USE ON RAW SENSOR DATA.
def lag(n):
    def lagged(timestamp, timestep, inputs):
        vals = next(iter(inputs.values()))
        ret = [(vals[i+n][0], vals[i+n][1], vals[i][2]) for i in range(len(vals)-n)]
        return ret
    return lagged

def max_value(timestamp, timestep, inputs):
    return (timestamp, timestep, max(next(iter(inputs.values()))))

def min_value(timestamp, timestep, inputs):
    return (timestamp, timestep, min(next(iter(inputs.values()))))

def chain(*functions):
    def chained(timestamp, timestep, inputs):
        for fun in functions:
            last = fun.__name__
            try:
                inputs = {f'__chained_{last}': fun(timestamp, timestep, inputs)}
            except Exception as e:
                # print(inputs)
                raise e
        return next(iter(inputs.values()))
    chained.__name__ = f"chained_function-{'-'.join([f.__name__ for f in functions])}"
    chained.__qualname__ = f"chained_function-{'-'.join([f.__name__ for f in functions])}"

    return chained

def fill_missing_with_nearby(timestamp, timestep, inputs):
    from math import isnan
    vals = next(iter(inputs.values()))
    
    missing_at_start = []

    output = []
    if vals:
        i = 0
        candidate_example = vals[0]
        # Find first example with non-missing value
        while candidate_example[2] == {}:
            missing_at_start.append(candidate_example)
            i += 1
            candidate_example = vals[i]
        
        fill_value = candidate_example[2]
        for m_ts, m_timestep, m_value in missing_at_start:
            output.append((m_ts, m_timestep, fill_value))
        
        while i < len(vals):
            e_ts, e_timestep, e_value = vals[i]
            if e_value == {}:
                output.append((e_ts, e_timestep, fill_value))
            else:
                output.append(vals[i])
                fill_value = e_value
            i += 1
    return output

def keyed_median(key=None):
    def median_f(timestamp, timestep, inputs):
        vals = [x[2] for x in next(iter(inputs.values()))]
        s_vals = []
        if key != None:
            s_vals = sorted(vals, key=key)
        else:
            s_vals = sorted(vals)
        return [(timestamp, timestep, s_vals[(len(s_vals) + 1) // 2])]
    return median_f

def median(timestamp, timestep, inputs):
    vals = [x[2] for x in next(iter(inputs.values()))]
    s_vals = sorted(vals)
    return [(timestamp, timestep, s_vals[(len(s_vals) + 1) // 2])]

def mode(timestamp, timestep, inputs):
    vals = [x[2] for x in next(iter(inputs.values()))]
    most = None
    n = float("-inf")
    for x in set(vals):
        if most is None or vals.count(x) > n:
            most = x
            n = vals.count(x)
    if most is None:
        raise ValueError
    return [(timestamp, timestep, most)]

def flat(fun, *args, **kwargs):
    """Flat use of function on an input list with single output."""
    def flattened(timestamp, timestep, inputs):
        vals = next(iter(inputs.values()))

        out = fun([val[2] for val in vals], *args, **kwargs)

        ret = [(timestamp, timestep, out)]
        return ret
    flattened.__name__ = f"""flattened[{fun.__name__}]"""
    flattened.__qualname__ = f"""flattened[{fun.__name__}]"""
    return flattened

def mapper(fun, *args, default=None, **kwargs):
    """Map function with *args and **kwargs to each value."""
    def mapped(timestamp, timestep, inputs):
        vals = next(iter(inputs.values()))

        def exc_fun(val, *args, **kwargs):
            try:
                return fun(val, *args, **kwargs)
            except Exception as e:
                if default is not None:
                    return default
                else:
                    raise e

        ret = [(timestamp, timestep, exc_fun(val, *args, **kwargs)) for timestamp, timestep, val in vals]
        return ret
    mapped.__name__ = f"""mapped[{fun.__name__}]"""
    mapped.__qualname__ = f"""mapped[{fun.__name__}]"""
    return mapped

def flat_fuse(timestamp, timestep, inputs):
    outputs = []
    for i in inputs:
        outputs += inputs[i]
    outputs.sort()
    return outputs


def count(timestamp, timestep, inputs):
    cnt = 0
    for k in inputs:
        cnt += len(inputs[k])
    return [(timestamp, timestep, cnt)]

def time_filter(time_start, time_end):
    """Time filter single-input functions."""

    def filtered(timestamp, timestep, inputs):
        start_timestamp = timestamp - human_time(time_start)
        end_timestamp = timestamp - human_time(time_end)

        vals = next(iter(inputs.values()))

        ret = [(ts, tstep, val) for ts, tstep, val in vals if start_timestamp <= ts < end_timestamp]

        return ret

    filtered.__name__ = f"""filtered[{time_start}-{time_end}]"""
    filtered.__qualname__ = f"""filtered[{time_start}-{time_end}]"""

    return filtered

def midnight_filter(timestamp, timestep, inputs):
    """Strips all values from inputs that are recorded before midnight."""
    values = next(iter(inputs.values()))
    dt = datetime.fromtimestamp(timestamp)
    timezone = profile_lookup('timezone')
    midnight = pytz.timezone(timezone).localize(datetime(year=dt.year, month=dt.month, day=dt.day)).timestamp()

    outputs = [(ts, tstep, val) for ts, tstep, val in values if ts >= midnight]

    return outputs

def load_profile(key):
    def load(timestamp, timestep, inputs):
        return [(timestamp, timestep, profile_lookup(key))]
    
    return load

def alias(timestamp, timestep, inputs):
    vals = next(iter(inputs.values()))
    return vals


def slicer(window):
    window = human_time(window)
    def sliced(timestamp, timestep, inputs):
        vals = []
        for k, g in groupby(next(iter(inputs.values())), lambda d: d[0] // window):
            vals.append(((k - 1) * window, window, [v for t, ts, v in list(g)]))
        return vals
    return sliced
