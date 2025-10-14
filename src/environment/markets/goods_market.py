"""
Goods Market for SimCity Simulation

財市場:
- 44種類の異質財の取引
- 価格メカニズム（需給調整）
- 在庫管理
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class GoodListing:
    """
    財の出品情報

    Attributes:
        firm_id: 企業ID
        good_id: 財ID（例: "food_basic"）
        quantity: 出品数量
        price: 単価
    """

    firm_id: int
    good_id: str
    quantity: float
    price: float


@dataclass
class GoodOrder:
    """
    財の注文情報

    Attributes:
        household_id: 世帯ID
        good_id: 財ID
        quantity: 注文数量
        max_price: 支払可能最高価格
    """

    household_id: int
    good_id: str
    quantity: float
    max_price: float


@dataclass
class Transaction:
    """
    取引結果

    Attributes:
        firm_id: 売り手企業ID
        household_id: 買い手世帯ID
        good_id: 財ID
        quantity: 取引数量
        price: 取引価格
        total_value: 取引総額
    """

    firm_id: int
    household_id: int
    good_id: str
    quantity: float
    price: float
    total_value: float


class GoodsMarket:
    """
    財市場

    44種類の財の取引を管理
    - 需給マッチング
    - 価格調整（オプション）
    - 在庫追跡
    """

    def __init__(self, enable_price_adjustment: bool = False):
        """
        Args:
            enable_price_adjustment: 価格調整を有効にするか
        """
        self.enable_price_adjustment = enable_price_adjustment

        # 統計情報
        self.total_listings = 0
        self.total_orders = 0
        self.total_transactions = 0
        self.total_volume = 0.0  # 取引総額
        self.unmet_demand: dict[str, float] = {}  # 財IDごとの未充足需要
        self.unsold_supply: dict[str, float] = {}  # 財IDごとの未売却在庫

        logger.info(
            f"GoodsMarket initialized: price_adjustment={enable_price_adjustment}"
        )

    def match(
        self,
        listings: list[GoodListing],
        orders: list[GoodOrder],
    ) -> list[Transaction]:
        """
        財の出品と注文をマッチング

        Args:
            listings: 出品リスト
            orders: 注文リスト

        Returns:
            取引リスト
        """
        self.total_listings += len(listings)
        self.total_orders += len(orders)

        transactions: list[Transaction] = []

        # 財IDごとにグループ化
        listings_by_good = self._group_by_good(listings)
        orders_by_good = self._group_by_good(orders)

        # 各財について需給マッチング
        for good_id in set(listings_by_good.keys()) | set(orders_by_good.keys()):
            good_listings = listings_by_good.get(good_id, [])
            good_orders = orders_by_good.get(good_id, [])

            # 価格順にソート
            sorted_listings = sorted(good_listings, key=lambda x: x.price)
            sorted_orders = sorted(good_orders, key=lambda x: -x.max_price)

            # マッチング処理
            good_transactions = self._match_good(sorted_listings, sorted_orders)
            transactions.extend(good_transactions)

            # 未充足需要と未売却在庫を記録
            total_supplied = sum(listing.quantity for listing in good_listings)
            total_demanded = sum(order.quantity for order in good_orders)
            total_sold = sum(txn.quantity for txn in good_transactions)

            self.unmet_demand[good_id] = max(0, total_demanded - total_sold)
            self.unsold_supply[good_id] = max(0, total_supplied - total_sold)

        self.total_transactions += len(transactions)
        self.total_volume += sum(t.total_value for t in transactions)

        logger.info(
            f"Goods market matching: {len(transactions)} transactions "
            f"from {len(listings)} listings and {len(orders)} orders"
        )

        return transactions

    def _group_by_good(
        self, items: list[GoodListing | GoodOrder]
    ) -> dict[str, list[Any]]:
        """
        財IDごとにグループ化

        Args:
            items: 出品または注文のリスト

        Returns:
            財IDをキーとした辞書
        """
        grouped: dict[str, list[Any]] = {}
        for item in items:
            if item.good_id not in grouped:
                grouped[item.good_id] = []
            grouped[item.good_id].append(item)
        return grouped

    def _match_good(
        self, listings: list[GoodListing], orders: list[GoodOrder]
    ) -> list[Transaction]:
        """
        特定の財の需給マッチング

        Args:
            listings: 出品リスト（価格昇順）
            orders: 注文リスト（価格降順）

        Returns:
            取引リスト
        """
        transactions = []

        # 出品と注文をマッチング
        for order in orders:
            for listing in listings:
                if listing.quantity <= 0:
                    continue

                # 価格条件チェック
                if listing.price > order.max_price:
                    break  # 価格が高すぎる

                # 取引数量を決定
                trade_quantity = min(listing.quantity, order.quantity)

                if trade_quantity > 0:
                    # 取引を記録
                    transaction = Transaction(
                        firm_id=listing.firm_id,
                        household_id=order.household_id,
                        good_id=listing.good_id,
                        quantity=trade_quantity,
                        price=listing.price,  # 売り手の提示価格
                        total_value=trade_quantity * listing.price,
                    )
                    transactions.append(transaction)

                    # 在庫と注文量を更新
                    listing.quantity -= trade_quantity
                    order.quantity -= trade_quantity

                    if order.quantity <= 0:
                        break  # 注文が完了

        return transactions

    def get_market_prices(self) -> dict[str, float]:
        """
        各財の市場価格を取得（直近の取引価格の平均）

        Returns:
            財IDをキーとした価格辞書
        """
        # 実際の実装では、過去の取引履歴から価格を計算
        # ここでは簡略化のため、空の辞書を返す
        return {}

    def get_statistics(self) -> dict[str, Any]:
        """
        市場統計を取得

        Returns:
            統計情報辞書
        """
        return {
            "total_listings": self.total_listings,
            "total_orders": self.total_orders,
            "total_transactions": self.total_transactions,
            "total_volume": self.total_volume,
            "num_goods_traded": len(self.unmet_demand),
            "total_unmet_demand": sum(self.unmet_demand.values()),
            "total_unsold_supply": sum(self.unsold_supply.values()),
        }

    def reset_statistics(self):
        """統計情報をリセット"""
        self.total_listings = 0
        self.total_orders = 0
        self.total_transactions = 0
        self.total_volume = 0.0
        self.unmet_demand.clear()
        self.unsold_supply.clear()
