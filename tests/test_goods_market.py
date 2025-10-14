"""Tests for Goods Market"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.markets.goods_market import GoodListing, GoodOrder, GoodsMarket, Transaction


class TestGoodsMarket:
    @pytest.fixture
    def market(self):
        return GoodsMarket()

    def test_basic_matching(self, market):
        listings = [GoodListing(firm_id=1, good_id="food_basic", quantity=100, price=10.0)]
        orders = [GoodOrder(household_id=101, good_id="food_basic", quantity=50, max_price=12.0)]
        
        transactions = market.match(listings, orders)
        
        assert len(transactions) == 1
        assert transactions[0].quantity == 50
        assert transactions[0].price == 10.0

    def test_price_filter(self, market):
        listings = [GoodListing(firm_id=1, good_id="food_basic", quantity=100, price=15.0)]
        orders = [GoodOrder(household_id=101, good_id="food_basic", quantity=50, max_price=10.0)]
        
        transactions = market.match(listings, orders)
        
        assert len(transactions) == 0

    def test_multiple_goods(self, market):
        listings = [
            GoodListing(firm_id=1, good_id="food_basic", quantity=100, price=10.0),
            GoodListing(firm_id=2, good_id="clothing_basic", quantity=50, price=20.0),
        ]
        orders = [
            GoodOrder(household_id=101, good_id="food_basic", quantity=50, max_price=12.0),
            GoodOrder(household_id=102, good_id="clothing_basic", quantity=30, max_price=25.0),
        ]
        
        transactions = market.match(listings, orders)
        
        assert len(transactions) == 2
        goods_traded = {t.good_id for t in transactions}
        assert "food_basic" in goods_traded
        assert "clothing_basic" in goods_traded

    def test_statistics(self, market):
        market.reset_statistics()
        
        listings = [GoodListing(firm_id=1, good_id="food_basic", quantity=100, price=10.0)]
        orders = [GoodOrder(household_id=101, good_id="food_basic", quantity=50, max_price=12.0)]
        
        transactions = market.match(listings, orders)
        stats = market.get_statistics()
        
        assert stats["total_listings"] == 1
        assert stats["total_orders"] == 1
        assert stats["total_transactions"] == 1
        assert stats["total_volume"] == 500.0  # 50 * 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
