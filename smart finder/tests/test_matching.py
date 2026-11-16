import unittest
from ai_engine.preprocessing import preprocess_text, build_item_text_corpus
from ai_engine.matching import RealAIMatchingEngine

class MockItem:
    def __init__(self, item_name, category, description, location, additional_details=""):
        self.item_name = item_name
        self.category = category
        self.description = description
        self.location = location
        self.additional_details = additional_details


class AIMatchingEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = RealAIMatchingEngine()

    def test_text_preprocessing(self):
        # Test punctuation removal, lowercasing, and stopword removal
        raw_text = "I lost my Black Water Bottles in the central Library yesterday!"
        cleaned = preprocess_text(raw_text)
        self.assertNotIn("!", cleaned)
        self.assertNotIn("i", cleaned.split())
        self.assertNotIn("in", cleaned.split())
        self.assertIn("black", cleaned)
        self.assertIn("water", cleaned)
        self.assertIn("bottle", cleaned)  # stemmed plural bottles -> bottle
        self.assertIn("library", cleaned)

    def test_empty_and_special_text_handling(self):
        # Must safely handle empty or whitespace without throwing errors
        self.assertEqual(preprocess_text(""), "")
        self.assertEqual(preprocess_text("   "), "")
        self.assertEqual(preprocess_text("!!!???"), "")

    def test_high_similarity_matching(self):
        # Lost and Found for the same water bottle
        lost = MockItem(
            item_name="Black Hydro Flask Water Bottle",
            category="Water Bottles & Flasks",
            description="I lost my matte black 750ml water bottle in the reading hall. Has NASA space sticker.",
            location="Central Library"
        )
        found = MockItem(
            item_name="Black Metal Water Bottle",
            category="Water Bottles & Flasks",
            description="Black water flask found sitting on a library table. Prominent NASA space sticker.",
            location="Central Library"
        )
        res = self.engine.compute_similarity(lost, found)
        
        # Must produce a significant match score
        self.assertGreaterEqual(res['overall_score'], 50.0)
        self.assertTrue(res['category_match'])
        self.assertTrue(res['location_match'])
        self.assertIn('black', res['shared_keywords'])
        self.assertIn('nasa', res['shared_keywords'])

    def test_unrelated_items_low_similarity(self):
        # Totally different items
        lost = MockItem(
            item_name="Silver Dell XPS Laptop",
            category="Electronics",
            description="Silver 15-inch laptop forgotten in CS computer lab 3.",
            location="Computer Science Lab"
        )
        found = MockItem(
            item_name="Red Woolen Scarf",
            category="Clothing & Accessories",
            description="Red knit winter muffler scarf found on bench outside sports complex.",
            location="Sports Complex & Ground"
        )
        res = self.engine.compute_similarity(lost, found)
        
        # Similarity should be very low
        self.assertLess(res['overall_score'], 25.0)
        self.assertFalse(res['category_match'])
        self.assertFalse(res['location_match'])

    def test_category_and_location_comparison(self):
        score, exact = self.engine.compare_categories("Electronics", "Electronics")
        self.assertEqual(score, 1.0)
        self.assertTrue(exact)

        score, exact = self.engine.compare_categories("Electronics", "Books & Stationery")
        self.assertEqual(score, 0.0)
        self.assertFalse(exact)

        score, exact = self.engine.compare_locations("Central Library", "Central Library")
        self.assertEqual(score, 1.0)
        self.assertTrue(exact)


if __name__ == '__main__':
    unittest.main()
