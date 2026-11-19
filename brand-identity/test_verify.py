"""Regression coverage for the artwork confirmation gate."""

import unittest

from verify import WEIGHTS, check_meaning_shortlists, validate_production


def meanings():
    return [
        {"layer": layer, "detail": detail, "meaning": interpretation, "anchor": "Synthetic brief"}
        for layer, detail, interpretation in (
            ("product", "Opening", "Shows the inspection step"),
            ("audience", "Held baseline", "Offers a stable point of comparison"),
            ("principle", "Paired outlines", "Makes edits visible beside the starting state"),
        )
    ]


def scored_decision():
    concepts = [
        {"id": f"concept-{index}", "category": "pictorial", "art_style": "relief print",
         "example": f"Distinct example {index}", "rationale": "Rated against the project brief",
         "scores": dict.fromkeys(WEIGHTS, index + 2), "meanings": meanings()}
        for index in range(3)
    ]
    return {
        "initial_category": "pictorial", "art_style": "relief print",
        "category_fit": {"pictorial": {"fits": True, "reason": "Recognizable silhouette"},
                         "emblem": {"fits": False, "reason": "Crowded at avatar size"}},
        "concepts": concepts, "selected_concept": "concept-2", "selection_reason": "Highest score",
        "names": {"product": "Example Toolkit", "wordmark": "EXAMPLE"},
        "name_options": [{"id": f"name-{i}", "text": text, "meanings": meanings()}
                         for i, text in enumerate(("Example Toolkit", "Sample Toolkit"))],
        "slogan_options": [{"id": f"slogan-{i}", "text": text, "meanings": meanings()}
                           for i, text in enumerate(("See the Example", "Open a Sample"))],
        "wordmark_options": [{"id": f"type-{i}", "text": "EXAMPLE", "treatment": style,
                              "meanings": meanings()}
                             for i, style in enumerate(("Hand cut", "Monospaced"))],
        "confirmation": {"product": "Example Toolkit", "wordmark": "EXAMPLE",
                         "reference": "Synthetic owner confirmation"},
    }


class ArtworkGateTests(unittest.TestCase):
    def test_template_and_pending_project_pass_inventory_checks(self):
        for kind in ("template", "project"):
            validate_production(kind, [], False, {"confirmation": None})

    def test_pending_name_blocks_artwork_and_asset_registration(self):
        decision = scored_decision()
        decision["confirmation"] = None
        for assets, ready in (([], True), ([{"role": "logo"}], False)):
            with self.subTest(ready=ready), self.assertRaisesRegex(ValueError, "name confirmation"):
                validate_production("project", assets, ready, decision)

    def test_category_and_comparison_are_required(self):
        decision = scored_decision()
        decision["category_fit"].pop("emblem")
        with self.assertRaisesRegex(ValueError, "alternative"):
            validate_production("project", [], True, decision)

    def test_shortlist_needs_three_examples(self):
        decision = scored_decision()
        decision["concepts"].pop()
        with self.assertRaisesRegex(ValueError, "three concept"):
            validate_production("project", [], True, decision)

    def test_lowest_scoring_concept_cannot_be_selected(self):
        decision = scored_decision()
        decision["selected_concept"] = "concept-0"
        with self.assertRaisesRegex(ValueError, "highest-scoring"):
            validate_production("project", [], True, decision)

    def test_exact_confirmation_must_match_current_name(self):
        for key, new_name in (("product", "Renamed Toolkit"), ("wordmark", "Example")):
            with self.subTest(key=key):
                decision = scored_decision()
                decision["names"][key] = new_name
                with self.assertRaisesRegex(ValueError, f"exact {key}"):
                    validate_production("project", [], True, decision)
                decision["confirmation"][key] = new_name
                shortlist = "name_options" if key == "product" else "wordmark_options"
                decision[shortlist][0]["text"] = new_name
                validate_production("project", [], True, decision)

    def test_boolean_score_is_rejected(self):
        decision = scored_decision()
        decision["concepts"][0]["scores"]["brand_fit"] = True
        with self.assertRaisesRegex(ValueError, "integer from 1 through 5"):
            validate_production("project", [], True, decision)

    def test_repeated_example_is_rejected(self):
        decision = scored_decision()
        decision["concepts"][1]["example"] = decision["concepts"][0]["example"]
        with self.assertRaisesRegex(ValueError, "must be distinct"):
            validate_production("project", [], True, decision)

    def test_each_list_requires_three_meanings_per_option(self):
        for shortlist in ("name_options", "concepts", "slogan_options", "wordmark_options"):
            with self.subTest(shortlist=shortlist):
                decision = scored_decision()
                decision[shortlist][0]["meanings"].pop()
                with self.assertRaisesRegex(ValueError, "at least three meanings"):
                    validate_production("project", [], True, decision)

    def test_distinct_meanings_and_all_layers_are_required(self):
        decision = scored_decision()
        first, second, last = decision["concepts"][0]["meanings"]
        last["meaning"] = first["meaning"].upper()
        with self.assertRaisesRegex(ValueError, "meanings must be distinct"):
            check_meaning_shortlists(decision)
        last["meaning"] = "A different reading"
        last["layer"] = second["layer"]
        with self.assertRaisesRegex(ValueError, "cover product, audience, and principle"):
            check_meaning_shortlists(decision)

    def test_single_previously_locked_name(self):
        decision = scored_decision()
        decision["name_options"].pop()
        with self.assertRaisesRegex(ValueError, "at least 2 options"):
            check_meaning_shortlists(decision)
        decision["existing_name_lock"] = "Synthetic prior name decision"
        check_meaning_shortlists(decision)

    def test_wordmark_must_include_exact_selected_text(self):
        decision = scored_decision()
        for wordmark in decision["wordmark_options"]:
            wordmark["text"] = "Example"
        with self.assertRaisesRegex(ValueError, "exact proposed wordmark"):
            check_meaning_shortlists(decision)

    def test_complete_record_allows_artwork(self):
        decision = scored_decision()
        validate_production("project", [], True, decision)
        validate_production("project", [{"role": "logo"}], False, decision)


if __name__ == "__main__":
    unittest.main()
