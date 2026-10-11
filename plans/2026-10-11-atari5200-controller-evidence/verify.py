"""Validate the recorded red baseline and bounded reference sweep, not a fix."""
from __future__ import annotations

import csv
import hashlib
import itertools
from collections.abc import Callable
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTS = (0, 1, 2, 3, 4, 5, 255)
KINDS = ('idle', 'fire1', 'x', 'y', 'fire2', 'keypad')


def read(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(newline='') as source:
        return list(csv.DictReader(source))


def check_guest(rows: list[dict[str, str]], debounce: bool) -> None:
    selectors = (0,) if debounce else range(4)
    controls = (1, 3) if debounce else (0, 2)
    expected = set(itertools.product(KINDS, PORTS, selectors, controls))
    actual = [(r['case'], int(r['port']), int(r['selected']), int(r['skctl'])) for r in rows]
    assert len(actual) == len(set(actual)) == len(expected), 'missing or duplicate guest case'
    assert set(actual) == expected, 'wrong guest coverage'
    failures = 0
    for r in rows:
        assert int(r['guest_loops']) > 100, 'guest did not repeatedly sample registers'
        assert r['passed'] in ('true', 'false')
        triggers = tuple(int(x, 16) for x in r['triggers'].split(':'))
        pots = tuple(int(x, 16) for x in r['pots'].split(':'))
        assert len(triggers) == 4 and set(triggers) <= {0, 1}
        assert len(pots) == 8 and all(0 <= x <= 228 for x in pots)
        if r['case'] == 'idle':
            assert triggers == (1, 1, 1, 1)
            assert int(r['seen_status'], 16) & 12 == 0
            assert r['passed'] == 'true'
        failures += r['passed'] == 'false'
    assert failures == (46 if debounce else 176), 'baseline mismatch accounting changed'


def check_reference(rows: list[dict[str, str]]) -> None:
    expected = set(itertools.product(range(1, 5), range(4), range(4), range(16), range(2)))
    keys = ('port', 'selected', 'skctl', 'key', 'top')
    actual = [tuple(int(r[k]) for k in keys) for r in rows]
    assert len(actual) == len(set(actual)) == len(expected), 'missing or duplicate reference case'
    assert set(actual) == expected
    for r in rows:
        port, selected, skctl, key, top = (int(r[k]) for k in keys)
        keypad = port - 1 == selected and key != 0 and skctl == 2
        upper = port - 1 == selected and top != 0 and bool(skctl & 2)
        assert int(r['seen_status']) == (4 if keypad else 0) | (8 if upper else 0)
        assert int(r['seen_irq']) == (64 if keypad else 0) | (128 if upper else 0)
        assert int(r['first_key_clock']) == ((key * 2 + 2) * 114 if keypad else 0)
        assert int(r['first_shift_clock']) == (17 * 114 if upper else 0)
        assert int(r['first_break_clock']) == (49 * 114 if upper else 0)
        assert int(r['key_irqs']) == (6 if keypad else 0)


def must_reject(check: Callable[[list[dict[str, str]]], None], rows: list[dict[str, str]]) -> None:
    try:
        check(rows)
    except AssertionError:
        return
    raise AssertionError('negative checker control unexpectedly passed')


def main() -> None:
    for line in (HERE / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    baseline = read('baseline.csv')
    check_guest(baseline, False)
    check_guest(read('debounce-baseline.csv'), True)
    reference = read('reference.csv')
    check_reference(reference)
    must_reject(check_reference, reference[:-1])
    must_reject(check_reference, [*reference, reference[0]])
    broken = [dict(r) for r in reference]
    broken[0]['seen_irq'] = '128'
    must_reject(check_reference, broken)
    broken_guest = [dict(r) for r in baseline]
    broken_guest[0]['guest_loops'] = '0'
    must_reject(lambda r: check_guest(r, False), broken_guest)
    assert '120 mismatches across 2048' in (HERE / 'reference-no-debounce.stderr').read_text()
    print('420 guest cases: 222 known failures; 2048 reference cases pass; four checker mutations rejected')


if __name__ == '__main__':
    main()
