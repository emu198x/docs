"""Independent synthetic controls for the bounded factory-pattern decoder."""

import unittest

from decode_patterns import cover, parse


def pins(*high: int) -> str:
    return "".join("1" if pin in high else "0" for pin in range(1, 61))


def setup(*, mask: str | None = None, direction: str | None = None) -> str:
    return (
        f"LSET D1 {direction or pins(41)}; LSET D2 {pins(41)};"
        f"LSET M1 {mask or pins(42)}; LSET M2 {pins()};"
        "ENABLE D1,M1,I1,TS1;"
    )


class CoverageTests(unittest.TestCase):
    def test_mask_direction_and_men_are_required(self) -> None:
        source = f"SET F {pins(41)};"
        for label, prefix, data, expected in [
            ("observed assertion", setup(), source, 1),
            ("masked", setup(mask=pins()), source, 0),
            ("input", setup(direction=pins(41, 42)), source, 0),
            ("disabled", setup(), f"SET F {pins()};", 0),
        ]:
            with self.subTest(label=label):
                result = cover(parse(prefix + data))
                self.assertEqual(len(result["enabled_nmi_low_candidates"]), expected)

    def test_normal_repeat_and_return_to_caller(self) -> None:
        source = (
            setup() + f"SET FC NORMAL 3 {pins(41, 42)};"
            f"SET F {pins(41, 42)} -LCALL SUB; SET F {pins(41, 42)};"
            f"LSUBR SUB NORMAL 2; SET F {pins(41)} -LEND;"
        )
        result = cover(parse(source))
        self.assertEqual(result["inventory"]["pattern_visits"], 7)
        self.assertEqual(result["inventory"]["checked_nmi_high"], 5)
        self.assertEqual(result["inventory"]["checked_nmi_low"], 2)
        self.assertEqual(len(result["enabled_nmi_low_candidates"]), 2)
        self.assertEqual(result["called_routines"], ["SUB"])

    def test_calls_use_current_register_values(self) -> None:
        # Compiler selection is fixed on the subroutine's SET F. Register
        # contents change at runtime, between the two calls to the same body.
        source = (
            setup(mask=pins()) + f"SET F {pins(41, 42)} -LCALL SUB; LSET M1 {pins(42)};"
            f"SET F {pins(41, 42)} -LCALL SUB;"
            f"LSUBR SUB NORMAL 1; SET F {pins(41)} -LEND;"
        )
        result = cover(parse(source))
        self.assertEqual(len(result["enabled_nmi_low_candidates"]), 1)
        self.assertEqual(result["inventory"]["checked_nmi_patterns"], 2)

    def test_normal_routine_register_writes_reach_caller(self) -> None:
        source = (
            setup(mask=pins()) + f"SET F {pins(41, 42)} -LCALL SUB; SET F {pins(41)};"
            f"LSUBR SUB NORMAL 1; LSET M1 {pins(42)}; SET F {pins(41, 42)} -LEND;"
        )
        result = cover(parse(source))
        self.assertEqual(len(result["enabled_nmi_low_candidates"]), 1)
        self.assertEqual(result["enabled_nmi_low_candidates"][0]["call_stack"], [])

    def test_match_is_unknown_multiplicity_not_fixed_repeat(self) -> None:
        source = (
            setup() + f"SET F {pins(41, 42)} -LCALL WAIT;"
            f"LSUBR WAIT MATCH 128; SET F {pins(41)} -LEND;"
        )
        result = cover(parse(source))
        self.assertEqual(result["inventory"]["pattern_visits"], 2)
        self.assertEqual(
            result["inventory"]["match_body_visits_unknown_multiplicity"], 1
        )
        self.assertTrue(result["enabled_nmi_low_candidates"][0]["match_uncertain"])

    def test_match_cannot_mutate_registers_even_through_nested_call(self) -> None:
        source = (
            setup() + f"SET F {pins(41, 42)} -LCALL WAIT;"
            f"LSUBR WAIT MATCH 128; SET F {pins(41, 42)} -LCALL WRITE; SET F {pins(41, 42)} -LEND;"
            f"LSUBR WRITE NORMAL 1; LSET M1 {pins()}; SET F {pins(41, 42)} -LEND;"
        )
        with self.assertRaisesRegex(ValueError, "MATCH register mutation"):
            cover(parse(source))

    def test_compile_selection_and_line_number(self) -> None:
        source = (
            setup()
            + f"\nENABLE M2,TS3;\nSET F {pins(41)};\nENABLE M1,TS2;\nSET F {pins(41)};"
        )
        result = cover(parse(source))
        self.assertEqual(
            result["enabled_nmi_low_candidates"],
            [
                {
                    "line": 5,
                    "timing": "TS2",
                    "call_stack": [],
                    "match_uncertain": False,
                    "halt": "0",
                    "pclk0": "0",
                }
            ],
        )

    def test_undefined_register_is_not_a_default(self) -> None:
        with self.assertRaisesRegex(ValueError, "undefined register"):
            cover(parse(f"SET F {pins(41)};"))

    def test_missing_or_recursive_call_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing routine"):
            parse(setup() + f"SET F {pins(41)} -LCALL MISSING;")
        source = (
            setup()
            + f"SET F {pins(41)} -LCALL SUB; LSUBR SUB NORMAL 1; SET F {pins(41)} -LCALL SUB; SET F {pins(41)} -LEND;"
        )
        with self.assertRaisesRegex(ValueError, "recursive routine"):
            cover(parse(source))

    def test_unknown_and_incomplete_input_fails(self) -> None:
        for source in [
            "ENABLE M3;",
            "ENABLE I2;",
            "SET FC MATCH 2 " + pins() + ";",
            "SET F " + "0" * 59 + ";",
            "SET F " + "0" * 61 + ";",
            "SET F " + pins(),
            "SET F " + pins() + "; UNPARSED",
            "LSUBR OPEN NORMAL 1;",
            "LSET D1 " + pins() + ";;",
            "SET F " + pins() + " -LEND;",
        ]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse(source)

    def test_unused_padding_cannot_become_called_code(self) -> None:
        source = (
            setup()
            + f"SET F {pins(41, 42)} -LCALL SUB; LSUBR SUB NORMAL 1; SET F {pins(41, 42)} -LEND; SET F {pins(41)};"
        )
        result = cover(parse(source))
        self.assertEqual(result["unexecuted_inter_routine_instructions"], 1)
        self.assertEqual(result["enabled_nmi_low_candidates"], [])


if __name__ == "__main__":
    unittest.main()
