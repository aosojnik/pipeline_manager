from .timeseries_tools import timeseries_tools


def vl_to_vl_wrapper(fun, *args, **kwargs):
    """Vector list to vector list wrapper. Used for features where each individual vector is processed into a new vector."""
    def vl2vl(timestamp, window, inputs):
        vals = next(iter(inputs.values()))

        raw = []
        raw.append([d[2]['x'] for d in vals])
        raw.append([d[2]['y'] for d in vals])
        raw.append([d[2]['z'] for d in vals])

        seq = fun(raw, *args, **kwargs)
        ret = [(vals[i][0], vals[i][1], {'x': seq[0][i], 'y': seq[1][i], 'z': seq[2][i]}) for i in range(len(seq[0]))]    
        return ret
    vl2vl.__name__ = f"""vl2vl[{fun.__name__}]"""
    vl2vl.__qualname__ = f"""vl2vl[{fun.__name__}]"""

    return vl2vl

def vl_to_sl_wrapper(fun, *args, **kwargs):
    """Vector list to scalar list wrapper. Used for features where each individual vector is processed into a new scalar."""
    def vl2sl(timestamp, window, inputs):
        f"""vl2sl wrapped {fun.__name__}"""
        vals = next(iter(inputs.values()))
        raw = []
        raw.append([d[2]['x'] for d in vals])
        raw.append([d[2]['y'] for d in vals])
        raw.append([d[2]['z'] for d in vals])

        seq = fun(raw, *args, **kwargs)

        ret = [(vals[i][0], vals[i][1], seq[0][i]) for i in range(len(seq[0]))] # seq[0] because many functions can calculate multiple scalar lists
        return ret
    vl2sl.__name__ = f"""vl2sl[{fun.__name__}]"""
    vl2sl.__qualname__ = f"""vl2sl[{fun.__name__}]"""

    return vl2sl

def sl_to_sl_wrapper(fun, *args, **kwargs):
    """Scalar list to scalar list wrapper. Used for features where each individual scalar is processed into a new scalar."""
    def sl2sl(timestamp, window, inputs):
        f"""sl2sl wrapped {fun.__name__}"""

        vals = next(iter(inputs.values()))

        seq = fun([val[2] for val in vals], *args, **kwargs)

        ret = [(vals[i][0], vals[i][1], seq[i]) for i in range(len(seq))]
        return ret
    sl2sl.__name__ = f"""sl2sl[{fun.__name__}]"""
    sl2sl.__qualname__ = f"""sl2sl[{fun.__name__}]"""

    return sl2sl

def sl_to_s_wrapper(fun, *args, **kwargs):
    """Scalar list to scalar wrapper. Used for features where the entire scalar list is processed into a single scalar."""
    def sl2s(timestamp, window, inputs):
        vals = next(iter(inputs.values()))

        seq = fun([[val[2] for val in vals]], *args, **kwargs) # seq[0] because many functions can calculate multiple scalar lists

        ret = [(timestamp, window, seq[0])]
        return ret
    sl2s.__name__ = f"""sl2s[{fun.__name__}]"""
    sl2s.__qualname__ = f"""sl2s[{fun.__name__}]"""
    return sl2s

def vl_to_v_wrapper(fun, *args, **kwargs):
    """Vector list to vector wrapper. Used for features where the entire vector list is processed into a single vector."""
    def vl2v(timestamp, window, inputs):
        vals = next(iter(inputs.values()))
        
        raw = []
        raw.append([d[2]['x'] for d in vals])
        raw.append([d[2]['y'] for d in vals])
        raw.append([d[2]['z'] for d in vals])

        seq = fun(raw, *args, **kwargs)

        ret = [(timestamp, window, {'x': seq[0], 'y': seq[1], 'z': seq[2]})]
        return ret
    
    vl2v.__name__ = f"""vl2v[{fun.__name__}]"""
    vl2v.__qualname__ = f"""vl2v[{fun.__name__}]"""
    return vl2v


low_pass_filter = vl_to_vl_wrapper(timeseries_tools.low_pass_filter, 0.1)
high_pass_filter = vl_to_vl_wrapper(timeseries_tools.high_pass_filter, 0.9)
band_pass_filter = vl_to_vl_wrapper(lambda x: timeseries_tools.high_pass_filter(timeseries_tools.low_pass_filter(x, 0.1), 0.9))

#magnitude = vl_to_sl_wrapper(timeseries_tools.calculate_magnitudes)
vector_mean = vl_to_v_wrapper(timeseries_tools.mean)
scalar_mean = sl_to_s_wrapper(timeseries_tools.mean)
total_mean = vl_to_sl_wrapper(timeseries_tools.total_mean)

area = vl_to_v_wrapper(timeseries_tools.area)
mean_absolute = vl_to_v_wrapper(timeseries_tools.mean_absolute)

mean_crossing_rate = sl_to_s_wrapper(timeseries_tools.mean_crossing_rate)

range_ = vl_to_v_wrapper(timeseries_tools.range_vector)

skewness = vl_to_v_wrapper(timeseries_tools.skewness)
kurtosis = vl_to_v_wrapper(timeseries_tools.kurtosis)

variance = vl_to_v_wrapper(timeseries_tools.calculate_variance)

def distance(timestamp, window, inputs):
    # The distance feature uses unique indexes and is coded separately
    vals = next(iter(inputs.values()))
    
    raw = []
    raw.append([d[2]['x'] for d in vals])
    raw.append([d[2]['y'] for d in vals])
    raw.append([d[2]['z'] for d in vals])

    seq = timeseries_tools.distance(raw)

    ret = [(timestamp, window, {'x-y': seq[0], 'x-z': seq[1], 'y-z': seq[2]})]
    return ret


def magnitude(timestamp, timestep, inputs):
    vals = next(iter(inputs.values()))

    return [(t, ts, (v['x'] ** 2 + v['y'] ** 2 + v['z'] ** 2) ** 0.5) for t, ts, v in vals if v != {}]

def magnitude_by_components(timestamp, timestep, inputs):
    value_lists = inputs.values()
    
    values = zip(*value_lists)

    def sqsum(triplets):
        return sum(t[2]**2 for t in triplets)
    
    return [(a[0][0], a[0][1], sqsum(a) ** 0.5) for a in values]
    

def peaks_size(timestamp, window, inputs):
    vals = next(iter(inputs.values()))

    raw = []
    raw.append([d[2] for d in vals])

    peaks, peak_counter, peak_size, peak_size_2 = timeseries_tools.peaks(raw, False)

    ret = [(timestamp, window, peak_size[0])]
    return ret
    
def sum_absolute_values(timestamp, window, inputs):
    vals = next(iter(inputs.values()))
    
    raw = []
    raw.append([d[2]['x'] for d in vals])
    raw.append([d[2]['y'] for d in vals])
    raw.append([d[2]['z'] for d in vals])

    sav_vec, sav_all = timeseries_tools.sum_absolute_signal(raw)

    ret = [(timestamp, window, {'x': sav_vec[0], 'y': sav_vec[1], 'z': sav_vec[2]})]
    return ret

def sum_absolute_values_all(timestamp, window, inputs):
    vals = next(iter(inputs.values()))
    
    raw = []
    raw.append([d[2]['x'] for d in vals])
    raw.append([d[2]['y'] for d in vals])
    raw.append([d[2]['z'] for d in vals])

    sav_vec, sav_all = timeseries_tools.sum_absolute_signal(raw)

    ret = [(timestamp, window, sav_vec[3])]
    return ret
