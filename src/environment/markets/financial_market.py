"""
Financial Market for SimCity Simulation

金融市場:
- 預金・貸出システム
- 金利計算（政策金利 + spread）
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class DepositRequest:
    """預金申請"""
    household_id: int
    amount: float


@dataclass
class LoanRequest:
    """貸出申請"""
    firm_id: int
    amount: float
    purpose: str  # "capital_investment", "working_capital"


@dataclass
class FinancialTransaction:
    """金融取引結果"""
    agent_id: int
    transaction_type: str  # "deposit", "loan"
    amount: float
    interest_rate: float


class FinancialMarket:
    """
    金融市場

    預金・貸出を管理
    - 政策金利に基づく金利決定
    - 預金金利 = 政策金利 - deposit_spread
    - 貸出金利 = 政策金利 + loan_spread
    """

    def __init__(
        self,
        policy_rate: float = 0.02,
        deposit_spread: float = -0.01,
        loan_spread: float = 0.02,
    ):
        """
        Args:
            policy_rate: 政策金利
            deposit_spread: 預金金利スプレッド（負の値）
            loan_spread: 貸出金利スプレッド（正の値）
        """
        self.policy_rate = policy_rate
        self.deposit_spread = deposit_spread
        self.loan_spread = loan_spread

        # 統計情報
        self.total_deposits = 0.0
        self.total_loans = 0.0
        self.deposit_count = 0
        self.loan_count = 0

        logger.info(
            f"FinancialMarket initialized: policy_rate={policy_rate:.2%}"
        )

    def get_deposit_rate(self) -> float:
        """預金金利を取得"""
        return max(0.0, self.policy_rate + self.deposit_spread)

    def get_loan_rate(self) -> float:
        """貸出金利を取得"""
        return self.policy_rate + self.loan_spread

    def process_deposits(
        self, requests: list[DepositRequest]
    ) -> list[FinancialTransaction]:
        """
        預金を処理

        Args:
            requests: 預金申請リスト

        Returns:
            取引結果リスト
        """
        transactions = []
        deposit_rate = self.get_deposit_rate()

        for req in requests:
            if req.amount > 0:
                transaction = FinancialTransaction(
                    agent_id=req.household_id,
                    transaction_type="deposit",
                    amount=req.amount,
                    interest_rate=deposit_rate,
                )
                transactions.append(transaction)
                self.total_deposits += req.amount
                self.deposit_count += 1

        logger.info(
            f"Processed {len(transactions)} deposits, "
            f"total amount: ${sum(t.amount for t in transactions):.2f}"
        )

        return transactions

    def process_loans(
        self, requests: list[LoanRequest]
    ) -> list[FinancialTransaction]:
        """
        貸出を処理

        Args:
            requests: 貸出申請リスト

        Returns:
            取引結果リスト
        """
        transactions = []
        loan_rate = self.get_loan_rate()

        for req in requests:
            if req.amount > 0:
                # 簡略化: 全ての貸出申請を承認
                transaction = FinancialTransaction(
                    agent_id=req.firm_id,
                    transaction_type="loan",
                    amount=req.amount,
                    interest_rate=loan_rate,
                )
                transactions.append(transaction)
                self.total_loans += req.amount
                self.loan_count += 1

        logger.info(
            f"Processed {len(transactions)} loans, "
            f"total amount: ${sum(t.amount for t in transactions):.2f}"
        )

        return transactions

    def update_policy_rate(self, new_rate: float):
        """政策金利を更新"""
        self.policy_rate = max(0.0, new_rate)
        logger.info(f"Policy rate updated to {self.policy_rate:.2%}")

    def get_statistics(self) -> dict[str, Any]:
        """市場統計を取得"""
        return {
            "policy_rate": self.policy_rate,
            "deposit_rate": self.get_deposit_rate(),
            "loan_rate": self.get_loan_rate(),
            "total_deposits": self.total_deposits,
            "total_loans": self.total_loans,
            "deposit_count": self.deposit_count,
            "loan_count": self.loan_count,
            "loan_to_deposit_ratio": (
                self.total_loans / self.total_deposits
                if self.total_deposits > 0
                else 0.0
            ),
        }

    def reset_statistics(self):
        """統計情報をリセット"""
        self.total_deposits = 0.0
        self.total_loans = 0.0
        self.deposit_count = 0
        self.loan_count = 0
