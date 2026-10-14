"""Explainable demo policy; model confidence is not probability of danger."""
import math


def assess(data):
    values = {}
    for key in ('gesture', 'scream', 'aggression'):
        v = data.get(key, 0)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
            raise ValueError(f'{key} must be a finite number from 0 to 1')
        values[key] = v
    manual = data.get('manual_sos', False)
    if not isinstance(manual, bool):
        raise ValueError('manual_sos must be boolean')
    reasons = [f'{key.capitalize()} signal above review threshold' for key, v in values.items() if v >= .7]
    if manual:
        return {'level': 'high', 'score': 100, 'reasons': ['Manual SOS requested']}
    confirmed = values['gesture'] >= .8 and values['scream'] >= .8
    score = round(100 * (.4 * values['gesture'] + .35 * values['scream'] + .25 * values['aggression']))
    level = 'high' if confirmed else 'moderate' if reasons else 'low'
    return {'level': level, 'score': score, 'reasons': reasons or ['No signal reached the review threshold']}
