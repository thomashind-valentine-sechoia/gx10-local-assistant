"""Unit tests for British-English TTS speech normalisation."""

from __future__ import annotations

import unittest

from speak_normalize import StreamingNormalizer, normalize_chunks, normalize_for_speech


VICTORIA_SPONGE = """
### Ingredients:
- 225g unsalted butter, softened
- 225g caster sugar
- 4 large eggs
- 225g self-raising flour
- 2 tsp baking powder
- 1/2 tsp vanilla extract
- 4 oz strawberry jam
- 1 tbsp icing sugar, to dust

### Method:
1. Preheat the oven to 180°C (160°C fan) and grease two 20cm tins.
2. Cream the butter and sugar until light and fluffy.
3. Beat in the eggs one at a time, then fold in the flour, baking powder and vanilla.
4. Bake for 20-25 minutes until golden.
""".strip()


class UnitsTests(unittest.TestCase):
    def test_teaspoon_singular_and_plural(self):
        self.assertEqual(normalize_for_speech("1 tsp vanilla"), "1 teaspoon vanilla")
        self.assertEqual(normalize_for_speech("add 1 tspn salt"), "add 1 teaspoon salt")
        self.assertEqual(normalize_for_speech("2 tsp baking powder"), "2 teaspoons baking powder")
        self.assertEqual(normalize_for_speech("2 tspn"), "2 teaspoons")

    def test_tablespoon(self):
        self.assertEqual(normalize_for_speech("1 tbsp icing sugar"), "1 tablespoon icing sugar")
        self.assertEqual(normalize_for_speech("2 tbs jam"), "2 tablespoons jam")
        self.assertEqual(normalize_for_speech("1 T butter"), "1 tablespoon butter")

    def test_attached_and_spaced_grams(self):
        self.assertEqual(normalize_for_speech("225g butter"), "225 grams butter")
        self.assertEqual(normalize_for_speech("225 g butter"), "225 grams butter")
        self.assertEqual(normalize_for_speech("1 g salt"), "1 gram salt")
        self.assertEqual(normalize_for_speech("1gr salt"), "1 gram salt")

    def test_kg_mg_ml_litre(self):
        self.assertEqual(normalize_for_speech("1 kg flour"), "1 kilogram flour")
        self.assertEqual(normalize_for_speech("2kg flour"), "2 kilograms flour")
        self.assertEqual(normalize_for_speech("500mg"), "500 milligrams")
        self.assertEqual(normalize_for_speech("150ml milk"), "150 millilitres milk")
        self.assertEqual(normalize_for_speech("2 l water"), "2 litres water")
        self.assertEqual(normalize_for_speech("1L stock"), "1 litre stock")
        self.assertEqual(normalize_for_speech("1 ltr milk"), "1 litre milk")

    def test_oz_lb_cm_mm_cl(self):
        self.assertEqual(normalize_for_speech("4 oz jam"), "4 ounces jam")
        self.assertEqual(normalize_for_speech("1oz"), "1 ounce")
        self.assertEqual(normalize_for_speech("2 lb butter"), "2 pounds butter")
        self.assertEqual(normalize_for_speech("1lb"), "1 pound")
        self.assertEqual(normalize_for_speech("two 20cm tins"), "two 20 centimetres tins")
        self.assertEqual(normalize_for_speech("5 mm"), "5 millimetres")
        self.assertEqual(normalize_for_speech("25cl"), "25 centilitres")

    def test_temperature_and_percent(self):
        self.assertEqual(
            normalize_for_speech("Preheat to 180°C"),
            "Preheat to 180 degrees Celsius",
        )
        self.assertEqual(
            normalize_for_speech("or 350°F"),
            "or 350 degrees Fahrenheit",
        )
        self.assertEqual(
            normalize_for_speech("fan 160°C"),
            "fan 160 degrees Celsius",
        )
        # Tight 180C without a degree sign is still a recipe temperature.
        self.assertEqual(normalize_for_speech("bake at 180C"), "bake at 180 degrees Celsius")
        self.assertEqual(normalize_for_speech("10% chance"), "10 percent chance")

    def test_does_not_touch_standalone_g_or_I(self):
        self.assertEqual(
            normalize_for_speech("The letter g is silent in gnaw. I agree."),
            "The letter g is silent in gnaw. I agree.",
        )
        self.assertIn("I went", normalize_for_speech("I went to the shop"))
        # 'great' must not become 'grams reat'
        self.assertEqual(normalize_for_speech("a great cake"), "a great cake")


class FractionRangeAndMiscTests(unittest.TestCase):
    def test_halves_and_mixed_numbers(self):
        self.assertEqual(normalize_for_speech("add 1/2 tsp"), "add a half teaspoon")
        self.assertEqual(normalize_for_speech("use ½ tsp"), "use a half teaspoon")
        self.assertEqual(normalize_for_speech("1 1/2 tsp"), "one and a half teaspoons")
        self.assertEqual(normalize_for_speech("2½ tsp"), "two and a half teaspoons")
        self.assertEqual(normalize_for_speech("¾ cup"), "three quarters cup")
        self.assertEqual(normalize_for_speech("¼ tsp"), "a quarter teaspoon")

    def test_range_and_multiplier(self):
        self.assertEqual(normalize_for_speech("Bake for 20-25 minutes"), "Bake for 20 to 25 minutes")
        self.assertEqual(normalize_for_speech("add 2-3 eggs"), "add 2 to 3 eggs")
        self.assertEqual(normalize_for_speech("make x2 the mixture"), "make times two the mixture")
        self.assertEqual(normalize_for_speech("batch ×2"), "batch times two")

    def test_times_are_preserved(self):
        self.assertEqual(
            normalize_for_speech("Set a timer for 12:30 and bake."),
            "Set a timer for 12:30 and bake.",
        )
        self.assertIn("12:30", normalize_for_speech("Meet at 12:30. Add 2 tsp."))

    def test_iso_date_not_treated_as_range(self):
        out = normalize_for_speech("Dated 2026-11-10 in the notes.")
        self.assertIn("2026-11-10", out)
        self.assertNotIn("to 11", out)

    def test_ampersand_approx_eg(self):
        self.assertEqual(
            normalize_for_speech("salt & pepper, approx. 1 tsp, e.g. sea salt"),
            "salt and pepper, approximately 1 teaspoon, for example sea salt",
        )


class MarkdownAndListTests(unittest.TestCase):
    def test_markdown_stripped(self):
        out = normalize_for_speech("**Ingredients:** `225g` flour from [BBC](https://bbc.co.uk/food)")
        self.assertIn("Ingredients:", out)
        self.assertIn("225 grams", out)
        self.assertIn("BBC", out)
        self.assertNotIn("http", out)
        self.assertNotIn("**", out)
        self.assertNotIn("`", out)

    def test_url_becomes_link(self):
        out = normalize_for_speech("See https://bbc.co.uk/food for more.")
        self.assertEqual(out, "See link for more.")

    def test_numbered_list_line_start(self):
        text = "1. Preheat the oven.\n2. Cream the butter.\n3. Bake."
        out = normalize_for_speech(text)
        self.assertIn("First, Preheat the oven.", out)
        self.assertIn("Second, Cream the butter.", out)
        self.assertIn("Third, Bake.", out)
        self.assertNotIn("1.", out)
        self.assertNotIn("2.", out)

    def test_inline_flattened_numbered_list(self):
        # HA / the current server join newlines into spaces.
        text = "1. Preheat the oven to 180°C and grease two 20cm tins. 2. Cream the butter. 3. Bake."
        out = normalize_for_speech(text)
        self.assertIn("First, Preheat", out)
        self.assertIn("Second, Cream", out)
        self.assertIn("Third, Bake", out)
        self.assertIn("180 degrees Celsius", out)
        self.assertIn("20 centimetres", out)

    def test_bullets_and_heading(self):
        text = "### Ingredients:\n- 225g butter\n- 2 tsp vanilla"
        out = normalize_for_speech(text)
        self.assertTrue(out.startswith("Ingredients:"))
        self.assertNotIn("#", out)
        self.assertIn("225 grams butter", out)
        self.assertIn("2 teaspoons vanilla", out)

    def test_eleventh_step(self):
        lines = "\n".join(f"{i}. Step text." for i in range(1, 12))
        out = normalize_for_speech(lines)
        self.assertIn("Tenth, Step text.", out)
        self.assertIn("Step eleven, Step text.", out)

    def test_decimal_not_a_list_marker(self):
        out = normalize_for_speech("Use 1.5 tsp of vanilla.")
        self.assertIn("1.5 teaspoons", out)
        self.assertNotIn("First", out)


class RecipeAndStreamingTests(unittest.TestCase):
    def test_victoria_sponge_recipe(self):
        out = normalize_for_speech(VICTORIA_SPONGE)
        # Units
        self.assertIn("225 grams unsalted butter", out)
        self.assertIn("2 teaspoons baking powder", out)
        self.assertIn("a half teaspoon vanilla", out)
        self.assertIn("4 ounces strawberry jam", out)
        self.assertIn("1 tablespoon icing sugar", out)
        self.assertIn("180 degrees Celsius", out)
        self.assertIn("160 degrees Celsius fan", out)
        self.assertIn("20 centimetres tins", out)
        self.assertIn("20 to 25 minutes", out)
        # Numbered method, not "1." with a spoken dot
        self.assertIn("First, Preheat the oven", out)
        self.assertIn("Second, Cream the butter", out)
        self.assertIn("Third, Beat in the eggs", out)
        self.assertIn("Fourth, Bake for", out)
        self.assertNotIn("1.", out)
        self.assertNotIn("2.", out)
        self.assertNotIn("3.", out)
        self.assertNotIn("4.", out)
        # Markdown gone
        self.assertNotIn("#", out)
        self.assertNotIn("**", out)

    def test_streaming_splits_list_marker_and_unit(self):
        # Token-sized chunks the way HA Assist can stream to Wyoming.
        chunks = [
            "1",
            ". Preheat the oven to 180",
            "°C and add 225",
            "g flour and 2",
            " tsp vanilla.\n2",
            ". Cream the butter.",
        ]
        out = normalize_chunks(chunks)
        self.assertIn("First, Preheat the oven", out)
        self.assertIn("180 degrees Celsius", out)
        self.assertIn("225 grams flour", out)
        self.assertIn("2 teaspoons vanilla", out)
        self.assertIn("Second, Cream the butter", out)
        self.assertNotIn("1.", out)

    def test_streaming_flush_at_end(self):
        stream = StreamingNormalizer()
        # Held because a trailing number may yet grow a unit.
        self.assertEqual(stream.feed("Add 225"), "")
        self.assertIn("225 grams", stream.feed("g flour."))
        self.assertEqual(stream.flush(), "")

    def test_empty(self):
        self.assertEqual(normalize_for_speech(""), "")
        self.assertEqual(normalize_for_speech("   "), "")


if __name__ == "__main__":
    unittest.main()
