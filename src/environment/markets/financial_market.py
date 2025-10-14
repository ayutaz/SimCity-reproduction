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
        max_loan_amount: float = 1_000_000.0,
        loan_to_deposit_ratio: float = 0.9,
    ):
        """
        Args:
            policy_rate: 政策金利
            deposit_spread: 預金金利スプレッド（負の値）
            loan_spread: 貸出金利スプレッド（正の値）
            max_loan_amount: 1回あたりの最大貸出額
            loan_to_deposit_ratio: 預貸率上限（総貸出/総預金）
        """
        self.policy_rate = policy_rate
        self.deposit_spread = deposit_spread
        self.loan_spread = loan_spread
        self.max_loan_amount = max_loan_amount
        self.loan_to_deposit_ratio_limit = loan_to_deposit_ratio

        # 統計情報
        self.total_deposits = 0.0
        self.total_loans = 0.0
        self.deposit_count = 0
        self.loan_count = 0
        self.rejected_loans = 0

        logger.info(
            f"FinancialMarket initialized: policy_rate={policy_rate:.2%}, "
            f"max_loan={max_loan_amount:,.0f}, LTD_limit={loan_to_deposit_ratio:.1%}"
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

    def process_loans(self, requests: list[LoanRequest]) -> list[FinancialTransaction]:
        """
        貸出を処理（Phase 9.10.1: 審査ロジック追加）

        審査基準:
        1. 貸出額上限チェック（max_loan_amount以下）
        2. 預貸率チェック（総貸出/総預金 ≤ loan_to_deposit_ratio_limit）

        Args:
            requests: 貸出申請リスト

        Returns:
            取引結果リスト（承認された貸出のみ）
        """
        transactions = []
        loan_rate = self.get_loan_rate()
        rejected_count = 0

        for req in requests:
            if req.amount <= 0:
                continue

            # 審査1: 貸出額上限チェック
            if req.amount > self.max_loan_amount:
                logger.debug(
                    f"Loan rejected (amount too large): firm={req.firm_id}, "
                    f"amount=${req.amount:,.0f} > limit=${self.max_loan_amount:,.0f}"
                )
                rejected_count += 1
                self.rejected_loans += 1
                continue

            # 審査2: 預貸率チェック
            if self.total_deposits > 0:
                new_total_loans = self.total_loans + req.amount
                new_ltd_ratio = new_total_loans / self.total_deposits

                if new_ltd_ratio > self.loan_to_deposit_ratio_limit:
                    logger.debug(
                        f"Loan rejected (LTD too high): firm={req.firm_id}, "
                        f"new_LTD={new_ltd_ratio:.2%} > limit={self.loan_to_deposit_ratio_limit:.2%}"
                    )
                    rejected_count += 1
                    self.rejected_loans += 1
                    continue

            # 承認: 貸出実行
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
            f"Processed {len(transactions)} loans (${sum(t.amount for t in transactions):.2f}), "
            f"rejected {rejected_count}"
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
            "rejected_loans": self.rejected_loans,
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
        self.rejected_loans = 0
