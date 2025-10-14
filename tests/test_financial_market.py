"""Tests for Financial Market"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.markets.financial_market import (
    DepositRequest,
    FinancialMarket,
    LoanRequest,
)


class TestFinancialMarket:
    @pytest.fixture
    def market(self):
        return FinancialMarket(policy_rate=0.02)

    def test_deposit_rate(self, market):
        rate = market.get_deposit_rate()
        assert rate == 0.01  # 0.02 - 0.01

    def test_loan_rate(self, market):
        rate = market.get_loan_rate()
        assert rate == 0.04  # 0.02 + 0.02

    def test_process_deposits(self, market):
        requests = [
            DepositRequest(household_id=101, amount=1000.0),
            DepositRequest(household_id=102, amount=2000.0),
        ]

        transactions = market.process_deposits(requests)

        assert len(transactions) == 2
        assert market.total_deposits == 3000.0

    def test_process_loans(self, market):
        requests = [
            LoanRequest(firm_id=1, amount=5000.0, purpose="capital_investment"),
            LoanRequest(firm_id=2, amount=3000.0, purpose="working_capital"),
        ]

        transactions = market.process_loans(requests)

        assert len(transactions) == 2
        assert market.total_loans == 8000.0

    def test_statistics(self, market):
        market.reset_statistics()

        deposits = [DepositRequest(household_id=101, amount=1000.0)]
        loans = [LoanRequest(firm_id=1, amount=500.0, purpose="capital_investment")]

        market.process_deposits(deposits)
        market.process_loans(loans)

        stats = market.get_statistics()

        assert stats["total_deposits"] == 1000.0
        assert stats["total_loans"] == 500.0
        assert stats["loan_to_deposit_ratio"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
