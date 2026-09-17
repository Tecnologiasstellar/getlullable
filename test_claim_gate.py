#!/usr/bin/env python3
"""The claim gate is the one thing standing between an unattended drafter and a
published health claim, so it gets the only test in this repo. Run: python3 test_claim_gate.py"""
import importlib.util, pathlib

spec = importlib.util.spec_from_file_location("build", pathlib.Path(__file__).parent / "build.py")
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
hits = b.prohibited_claims_in

CASES = [
    # (text, should_trip)
    ("This will help you sleep better tonight.",            True),
    ("Clinically proven to treat insomnia.",                True),
    ("Esta historia te ayudara a dormir mejor.",            True),
    ("Te ayudará a dormir mejor.",                          True),   # accents must not bypass
    ("Clínicamente probado para el insomnio.",              True),
    ("Dormirás más rápido con esto.",                       True),
    ("It will help you\nsleep better.",                     True),   # line break inside the phrase
    ("Lullable is not a treatment for insomnia.",           False),  # negated
    ("Lullable no es un tratamiento para el insomnio.",     False),  # negated, Spanish
    ("Esto no te ayuda a dormir y no lo prometemos.",       False),
    ("The voice is flat and the ending is given away.",     False),
    ("La voz es plana y el final se cuenta al principio.",  False),
]

def main():
    bad = 0
    for text, should in CASES:
        got = bool(hits(text))
        if got != should:
            bad += 1
            print(f"FAIL want={'trip' if should else 'clean'} got={hits(text) or 'clean'}: {text!r}")
    # no existing post may trip the gate — a change that breaks the catalogue is a
    # change that will be reverted at 3am instead of caught here
    for f in sorted((pathlib.Path(__file__).parent / "posts").glob("*.md")):
        h = hits(f.read_text())
        if h:
            bad += 1
            print(f"FAIL published post now trips the gate: {f.name} -> {h}")
    print(f"{len(CASES)} cases + every published post: {'OK' if not bad else f'{bad} FAILURES'}")
    raise SystemExit(1 if bad else 0)

if __name__ == "__main__":
    main()
