from django.test import TestCase

from .categorization import classify_transaction, learn_merchant_mapping
from .models import MerchantCategoryMapping


class CategorizationTests(TestCase):
	def test_keyword_match(self):
		category, sub_category, confidence, strategy = classify_transaction('Payment to Zomato', '')
		self.assertEqual(category, 'Food')
		self.assertEqual(sub_category, 'Restaurant')
		self.assertEqual(strategy, 'keyword')
		self.assertGreaterEqual(confidence, 0.9)

	def test_fuzzy_match(self):
		category, sub_category, confidence, strategy = classify_transaction('netflx', '')
		self.assertEqual(category, 'Entertainment')
		self.assertEqual(sub_category, 'Other')
		self.assertEqual(strategy, 'fuzzy')
		self.assertGreaterEqual(confidence, 0.72)

	def test_learned_mapping_is_reused(self):
		learn_merchant_mapping('Coffee Club', 'Food', 'Restaurant', source='test')
		category, sub_category, confidence, strategy = classify_transaction('coffee club', '')
		self.assertEqual(category, 'Food')
		self.assertEqual(sub_category, 'Restaurant')
		self.assertEqual(strategy, 'learned')
		self.assertEqual(confidence, 1.0)

	def test_unknown_fallback(self):
		category, sub_category, confidence, strategy = classify_transaction('unmapped vendor', '')
		self.assertEqual(category, 'Unknown')
		self.assertEqual(sub_category, 'Unknown')
		self.assertEqual(strategy, 'fallback')
		self.assertLess(confidence, 0.72)

	def test_learning_updates_usage_count(self):
		learn_merchant_mapping('Quick Mart', 'Personal', 'Others', source='test')
		learn_merchant_mapping('Quick Mart', 'Personal', 'Others', source='test')
		mapping = MerchantCategoryMapping.objects.get(merchant_key='quick mart')
		self.assertEqual(mapping.times_used, 2)
