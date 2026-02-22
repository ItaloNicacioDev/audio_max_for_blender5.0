from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter


# -------------------------------------------------
# BAND EQ
# -------------------------------------------------

def apply_lowpass(segment: AudioSegment, cutoff: float) -> AudioSegment:
    """
    Aplica filtro passa-baixa.
    """
    return low_pass_filter(segment, cutoff)


def apply_highpass(segment: AudioSegment, cutoff: float) -> AudioSegment:
    """
    Aplica filtro passa-alta.
    """
    return high_pass_filter(segment, cutoff)


# -------------------------------------------------
# SIMPLE 3-BAND EQ
# -------------------------------------------------

def apply_3band_eq(segment: AudioSegment, low_gain=0.0, mid_gain=0.0, high_gain=0.0):
    """
    Equalizador simples:
    - Low  < 200 Hz
    - Mid  200 - 4000 Hz
    - High > 4000 Hz
    """

    low = low_pass_filter(segment, 200) + low_gain

    high = high_pass_filter(segment, 4000) + high_gain

    mid = high_pass_filter(segment, 200)
    mid = low_pass_filter(mid, 4000) + mid_gain

    combined = low.overlay(mid).overlay(high)

    return combined


# -------------------------------------------------
# MULTI BAND EQ (ESCALÁVEL)
# -------------------------------------------------

def apply_multiband_eq(segment: AudioSegment, bands: list):
    """
    bands = [
        {"type": "lowpass", "freq": 200, "gain": 3},
        {"type": "band", "low": 200, "high": 2000, "gain": -2},
        {"type": "highpass", "freq": 5000, "gain": 4},
    ]
    """

    result = AudioSegment.silent(duration=len(segment))

    for band in bands:

        if band["type"] == "lowpass":
            processed = low_pass_filter(segment, band["freq"])

        elif band["type"] == "highpass":
            processed = high_pass_filter(segment, band["freq"])

        elif band["type"] == "band":
            processed = high_pass_filter(segment, band["low"])
            processed = low_pass_filter(processed, band["high"])

        else:
            continue

        gain = band.get("gain", 0.0)
        processed = processed + gain

        result = result.overlay(processed)

    return result

#aplly EQ
def apply_eq(segment: AudioSegment, mode="3band", **kwargs):
    """
    Wrapper genérico de EQ.
    """

    if mode == "3band":
        return apply_3band_eq(segment, **kwargs)

    if mode == "multiband":
        return apply_multiband_eq(segment, kwargs.get("bands", []))

    return segment