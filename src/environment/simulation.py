"""
Simulation engine for SimCity

シミュレーションのメインループと状態管理を提供
"""

import json
import random
from pathlib import Path

from loguru import logger

from src.agents.central_bank import CentralBankAgent
from src.agents.firm import FirmAgent, FirmTemplateLoader
from src.agents.government import GovernmentAgent
from src.agents.household import HouseholdAgent, HouseholdProfileGenerator
from src.environment.markets.financial_market import FinancialMarket
from src.environment.markets.goods_market import GoodListing, GoodOrder, GoodsMarket
from src.environment.markets.labor_market import JobPosting, JobSeeker, LaborMarket
from src.llm.llm_interface import LLMInterface
from src.models.data_models import (
    CentralBankState,
    FirmProfile,
    GovernmentState,
    HouseholdProfile,
    MarketState,
    SimulationState,
)
from src.models.economic_models import MacroeconomicIndicators
from src.utils.config import SimCityConfig, get_api_key


class Simulation:
    """
    SimCityシミュレーションエンジン

    論文のAlgorithm 1に基づくシミュレーションループ:
    1. Production and Trading Stage
    2. Taxation and Dividend Stage
    3. Metabolic Stage (人口流入・流出)
    4. Revision Stage (LLMによる意思決定)
    """

    def __init__(self, config: SimCityConfig):
        """
        Args:
            config: シミュレーション設定
        """
        self.config = config
        self.state = SimulationState()

        # 初期化
        self._initialize_state()

        logger.info(
            f"Simulation initialized: phase={self.state.phase}, "
            f"max_steps={config.simulation.max_steps}"
        )

    def _initialize_state(self):
        """シミュレーション状態の初期化"""
        self.state.step = 0
        self.state.phase = "move_in"

        # LLMインターフェースの初期化（環境変数から直接取得）
        llm_config = {
            "api_key": get_api_key("OPENAI_API_KEY"),
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        self.llm_interface = LLMInterface(llm_config)

        # エージェントの初期化
        self._initialize_agents()

        # 市場の初期化
        self._initialize_markets()

        # 履歴の初期化
        self.state.history = {
            "gdp": [],
            "real_gdp": [],
            "inflation": [],
            "unemployment_rate": [],
            "gini": [],
            "policy_rate": [],
            "num_households": [],
            "num_firms": [],
            "vacancy_rate": [],
            "consumption": [],
            "investment": [],
            "household_incomes": [],
            "food_expenditure_ratios": [],
            "prices": {},
            "demands": {},
        }

        # 基準年価格（ステップ0で設定）
        self.base_year_prices = None

        logger.info("State initialized")

    def _initialize_agents(self):
        """エージェントの初期化"""
        logger.info("Initializing agents...")

        # 世帯エージェントの初期化
        household_data_file = Path("data/initial_households.json")
        if household_data_file.exists():
            # データファイルから読み込み
            with open(household_data_file, encoding="utf-8") as f:
                household_data = json.load(f)
                household_profiles = household_data.get("households", [])

            self.households = [
                HouseholdAgent(
                    household_id=profile["id"],
                    profile=HouseholdProfile(**profile),
                    llm_interface=self.llm_interface,
                )
                for profile in household_profiles[
                    : self.config.agents.households.initial
                ]
            ]
        else:
            # プロファイルを生成
            generator = HouseholdProfileGenerator(
                random_seed=self.config.simulation.random_seed
            )
            profiles = generator.generate(count=self.config.agents.households.initial)

            self.households = [
                HouseholdAgent(
                    household_id=profile.household_id,
                    profile=profile,
                    llm_interface=self.llm_interface,
                )
                for profile in profiles
            ]

        # 企業エージェントの初期化
        logger.info("Initializing firms...")

        # 企業テンプレートを読み込み
        try:
            templates = FirmTemplateLoader.load_templates()

            # ランダムシードを設定
            random.seed(self.config.simulation.random_seed)

            # 初期企業数分をランダムに選択
            num_initial_firms = self.config.agents.firms.initial
            if num_initial_firms > len(templates):
                logger.warning(
                    f"Requested {num_initial_firms} firms, but only {len(templates)} "
                    f"templates available. Using all templates."
                )
                num_initial_firms = len(templates)

            selected_templates = random.sample(
                list(templates.items()),
                k=num_initial_firms
            )

            # 企業エージェントを生成
            self.firms = []
            city_center = (50, 50)  # デフォルト都市中心

            for i, (firm_id, template) in enumerate(selected_templates):
                # プロファイル生成
                profile = FirmTemplateLoader.create_firm_profile(
                    firm_id=str(i + 1),  # 連番ID
                    template=template,
                    location=city_center
                )

                # エージェント初期化
                firm_agent = FirmAgent(
                    profile=profile,
                    llm_interface=self.llm_interface
                )

                self.firms.append(firm_agent)

                logger.info(
                    f"  Firm {i + 1}: {profile.name} ({profile.goods_type}), "
                    f"Capital: ${profile.cash:.2f}, TFP: {profile.total_factor_productivity:.2f}"
                )

            logger.info(f"Initialized {len(self.firms)} firms")

        except FileNotFoundError as e:
            logger.error(f"Failed to load firm templates: {e}")
            logger.warning("Simulation will continue without firms")
            self.firms = []

        # 政府エージェントの初期化
        # 税率区分をdict形式からtuple形式に変換
        tax_brackets = [
            (bracket["threshold"], bracket["rate"])
            for bracket in self.config.economy.taxation.income_tax_brackets
        ]
        gov_state = GovernmentState(
            income_tax_brackets=tax_brackets,
            vat_rate=self.config.economy.taxation.vat_rate,
            ubi_enabled=self.config.economy.welfare.ubi_enabled,
            ubi_amount=self.config.economy.welfare.ubi_amount,
            unemployment_benefit_rate=self.config.economy.welfare.unemployment_benefit_rate,
        )
        self.government = GovernmentAgent(
            state=gov_state,
            llm_interface=self.llm_interface,
        )

        # 中央銀行エージェントの初期化
        cb_state = CentralBankState(
            policy_rate=self.config.economy.financial.initial_interest_rate,
            smoothing_factor=self.config.economy.financial.interest_rate_smoothing,
            natural_rate=self.config.economy.financial.taylor_rule.natural_rate,
            inflation_target=self.config.economy.financial.taylor_rule.inflation_target,
            taylor_alpha=self.config.economy.financial.taylor_rule.inflation_coefficient,
            taylor_beta=self.config.economy.financial.taylor_rule.output_coefficient,
        )
        self.central_bank = CentralBankAgent(
            state=cb_state,
            llm_interface=self.llm_interface,
        )

        # SimulationStateに設定
        self.state.households = [h.profile for h in self.households]
        self.state.firms = [f.profile for f in self.firms]
        self.state.government = gov_state
        self.state.central_bank = cb_state

        logger.info(
            f"Agents initialized: {len(self.households)} households, {len(self.firms)} firms"
        )

    def _initialize_markets(self):
        """市場の初期化"""
        logger.info("Initializing markets...")

        # 労働市場（必要なパラメータのみ抽出）
        labor_config = self.config.markets.labor.model_dump()
        labor_params = {
            k: v
            for k, v in labor_config.items()
            if k
            in ["matching_probability", "consider_distance", "max_commute_distance"]
        }
        self.labor_market = LaborMarket(**labor_params)

        # 財市場（必要なパラメータのみ抽出）
        goods_config = self.config.markets.goods.model_dump()
        goods_params = {
            k: v
            for k, v in goods_config.items()
            if k in ["price_adjustment_speed", "demand_elasticity", "inventory_target"]
        }
        self.goods_market = GoodsMarket(**goods_params)

        # 金融市場（必要なパラメータのみ抽出）
        financial_config = self.config.markets.financial.model_dump()
        financial_params = {
            k: v
            for k, v in financial_config.items()
            if k in ["default_deposit_rate", "default_loan_rate", "reserve_requirement"]
        }
        self.financial_market = FinancialMarket(**financial_params)

        self.state.market = MarketState()

        logger.info("Markets initialized")

    def step(self) -> dict[str, float]:
        """
        1ステップ（1ヶ月）を実行

        Returns:
            現在のマクロ経済指標
        """
        logger.info(f"=== Step {self.state.step} ===")

        # フェーズ管理
        if self.state.step >= self.config.simulation.phase1_steps:
            if self.state.phase == "move_in":
                self.state.phase = "development"
                logger.info("Phase transition: move_in -> development")

        # シミュレーションループ（簡略版）
        # 実際のエージェント実装はPhase 2で行う

        # Stage 1: Production and Trading
        self._production_and_trading_stage()

        # Stage 2: Taxation and Dividend
        self._taxation_and_dividend_stage()

        # Stage 3: Metabolic Stage
        if self.state.phase == "move_in":
            self._metabolic_stage()

        # Stage 4: Revision Stage (エージェント意思決定)
        self._revision_stage()

        # マクロ経済指標の計算
        indicators = self._calculate_indicators()

        # 履歴に記録
        self._record_history(indicators)

        # ステップカウンタ更新
        self.state.step += 1

        logger.info(f"Step {self.state.step - 1} completed")
        logger.info(
            f"Indicators: GDP={indicators['gdp']:.2f}, "
            f"Unemployment={indicators['unemployment_rate']:.2%}"
        )

        return indicators

    def _production_and_trading_stage(self):
        """
        Stage 1: 生産と取引

        企業が財を生産し、家計が購入
        """
        logger.debug("Production and Trading Stage")

        # 1. 企業が生産して出品
        listings = []
        for firm in self.firms:
            # 生産能力を計算
            capacity = firm.calculate_production_capacity()

            # 初期生産量（生産能力の50%）
            production_qty = capacity * 0.5 if capacity > 0 else 100.0

            # 在庫に追加
            firm.profile.inventory += production_qty
            firm.profile.production_quantity = production_qty

            # 出品（在庫の80%を出品）
            if firm.profile.inventory > 0:
                listing_qty = firm.profile.inventory * 0.8
                listing = GoodListing(
                    firm_id=firm.profile.id,
                    good_id=firm.profile.goods_type,
                    quantity=listing_qty,
                    price=firm.profile.price
                )
                listings.append(listing)

        # 2. 世帯が消費注文
        orders = []
        for household in self.households:
            # 消費予算（月収の80%）
            budget = household.profile.monthly_income * 0.8
            if budget <= 0:
                continue

            # 簡略版: 利用可能な財からランダムに1つ選択
            if listings:
                # ランダムに財を選択
                target_listing = random.choice(listings)

                # 購入数量を決定（予算内で）
                affordable_qty = budget / target_listing.price
                order_qty = min(affordable_qty, target_listing.quantity)

                if order_qty > 0:
                    order = GoodOrder(
                        household_id=household.profile.id,
                        good_id=target_listing.good_id,
                        quantity=order_qty,
                        max_price=target_listing.price * 1.2  # 20%まで高く払える
                    )
                    orders.append(order)

        # 3. 市場マッチング
        transactions = self.goods_market.match(listings, orders)

        # 4. 取引結果を反映
        total_consumption = 0.0

        # 財の種類判定用にインポート
        from src.data.goods_types import get_good
        from src.models.data_models import GoodCategory

        for txn in transactions:
            # 企業側: 収入増加、在庫減少
            for firm in self.firms:
                if firm.profile.id == txn.firm_id:
                    firm.profile.cash += txn.total_value
                    firm.profile.inventory -= txn.quantity
                    firm.profile.sales_quantity += txn.quantity
                    break

            # 世帯側: 支出記録
            for household in self.households:
                if household.profile.id == txn.household_id:
                    # consumption属性を追加（動的）
                    if not hasattr(household, 'consumption'):
                        household.consumption = 0.0
                    household.consumption += txn.total_value
                    total_consumption += txn.total_value

                    # 食料支出と総支出を追跡
                    if not hasattr(household, 'food_spending'):
                        household.food_spending = 0.0
                    if not hasattr(household, 'total_spending'):
                        household.total_spending = 0.0

                    household.total_spending += txn.total_value

                    # 財が食料カテゴリかチェック
                    good_def = get_good(txn.good_id)
                    if good_def and good_def.category == GoodCategory.FOOD:
                        household.food_spending += txn.total_value

                    break

        logger.info(
            f"Production & Trading: {len(transactions)} transactions, "
            f"total consumption: ${total_consumption:.2f}"
        )

    def _taxation_and_dividend_stage(self):
        """
        Stage 2: 課税と配当

        政府が税金を徴収し、UBI等を配分
        企業が配当を支払う
        """
        logger.debug("Taxation and Dividend Stage")

        # 1. 所得税徴収
        total_income_tax = 0.0
        for household in self.households:
            if household.profile.monthly_income > 0:
                tax = self.government.collect_income_tax(household.profile.monthly_income)
                total_income_tax += tax
                # 世帯の収入から差し引き（簡略版）

        # 2. VAT徴収（取引総額から）
        total_vat = 0.0
        total_transactions = sum(
            getattr(h, 'consumption', 0.0) for h in self.households
        )
        if total_transactions > 0:
            total_vat = self.government.collect_vat(total_transactions)

        # 3. 政府の税収を更新
        self.government.state.tax_revenue = total_income_tax + total_vat

        # 4. UBI配布
        ubi_expenditure = 0.0
        if self.government.state.ubi_enabled:
            ubi_expenditure = self.government.distribute_ubi(len(self.households))
            # 各世帯にUBIを付与
            for household in self.households:
                household.profile.monthly_income += self.government.state.ubi_amount

        # 5. 失業給付
        unemployment_expenditure = 0.0
        for household in self.households:
            if household.profile.employment_status == "unemployed":
                # 失業給付（前職賃金の50%、簡略版では月収の50%）
                benefit = self.government.calculate_unemployment_benefit(
                    household.profile.monthly_income,
                    months_unemployed=1  # 簡略版
                )
                unemployment_expenditure += benefit
                household.profile.monthly_income += benefit

        # 6. 企業配当（純利益の10%）
        total_dividends = 0.0
        for firm in self.firms:
            # 純利益 = 売上 - コスト（賃金）
            revenue = firm.profile.cash
            # 簡略版: 配当は現金の1%
            dividend = max(0, revenue * 0.01)
            firm.profile.cash -= dividend
            total_dividends += dividend

        # 7. 政府支出を更新
        self.government.state.expenditure = (
            ubi_expenditure + unemployment_expenditure + total_dividends
        )

        # 8. 政府準備金を更新
        budget_balance = self.government.state.tax_revenue - self.government.state.expenditure
        self.government.state.reserves += budget_balance

        logger.info(
            f"Taxation & Dividend: Tax=${total_income_tax + total_vat:.2f}, "
            f"Spending=${self.government.state.expenditure:.2f}, "
            f"Balance=${budget_balance:.2f}"
        )

    def _metabolic_stage(self):
        """
        Stage 3: 代謝ステージ

        新しい家計が流入
        """
        logger.debug("Metabolic Stage")

        max_households = self.config.agents.households.max
        current_households = len(self.households)
        monthly_inflow = self.config.agents.households.monthly_inflow

        if current_households < max_households:
            new_count = min(monthly_inflow, max_households - current_households)

            if new_count > 0:
                # 新規世帯を生成
                generator = HouseholdProfileGenerator(
                    random_seed=self.config.simulation.random_seed + self.state.step
                )
                new_profiles = generator.generate(count=new_count)

                # HouseholdAgentを初期化して追加
                for profile in new_profiles:
                    new_household = HouseholdAgent(
                        household_id=profile.id,
                        profile=profile,
                        llm_interface=self.llm_interface
                    )
                    self.households.append(new_household)
                    self.state.households.append(profile)

                logger.info(f"Metabolic: Added {new_count} new households (total: {len(self.households)})")

    def _revision_stage(self):
        """
        Stage 4: 意思決定ステージ

        エージェントが意思決定を行う（簡略版: LLMなし）
        """
        logger.debug("Revision Stage (simplified)")

        # 1. 企業: 価格調整
        for firm in self.firms:
            # 価格を±5%でランダム調整
            adjustment = random.uniform(-0.05, 0.05)
            firm.profile.price *= (1 + adjustment)
            firm.profile.price = max(1.0, firm.profile.price)  # 最低価格1.0

            # 求人枠の調整（従業員が0の場合は募集）
            num_employees = len(firm.profile.employees)
            target_employees = 5  # 簡略版: 各企業5人目標
            if num_employees < target_employees:
                firm.profile.job_openings = target_employees - num_employees
            else:
                firm.profile.job_openings = 0

        # 2. 労働市場マッチング
        # 求人を収集
        job_postings = []
        for firm in self.firms:
            if firm.profile.job_openings > 0:
                posting = JobPosting(
                    firm_id=firm.profile.id,
                    num_openings=firm.profile.job_openings,
                    wage_offered=firm.profile.wage_offered,
                    skill_requirements=firm.profile.skill_requirements,
                    location=firm.profile.location
                )
                job_postings.append(posting)

        # 求職者を収集（失業者のみ）
        job_seekers = []
        for household in self.households:
            if household.profile.employment_status == "unemployed":
                # 最低賃金は月収の80%（簡略版）
                reservation_wage = household.profile.monthly_income * 0.8
                if reservation_wage < 1000:  # 最低希望賃金
                    reservation_wage = 1000

                seeker = JobSeeker(
                    household_id=household.profile.id,
                    skills=household.profile.skills,
                    reservation_wage=reservation_wage,
                    location=household.profile.location,
                    currently_employed=False
                )
                job_seekers.append(seeker)

        # 労働市場マッチング実行
        if job_postings and job_seekers:
            matches = self.labor_market.match(job_postings, job_seekers)

            # マッチング結果を反映
            for match in matches:
                # 企業側: 従業員追加
                for firm in self.firms:
                    if firm.profile.id == match.firm_id:
                        firm.profile.employees.append(match.household_id)
                        firm.profile.job_openings -= 1
                        break

                # 世帯側: 雇用状態更新
                for household in self.households:
                    if household.profile.id == match.household_id:
                        household.profile.employment_status = "employed"
                        household.profile.monthly_income = match.wage
                        household.profile.employer_id = match.firm_id
                        break

            logger.info(f"Revision: {len(matches)} labor matches")
        else:
            logger.debug("Revision: No labor matching (no postings or seekers)")

        # 3. 金融市場統合
        self._financial_stage()

    def _financial_stage(self):
        """
        金融市場統合

        世帯の預金と企業の借入を処理
        """
        logger.debug("Financial Stage")

        # 1. 政策金利の更新
        if self.central_bank and self.central_bank.state:
            self.financial_market.update_policy_rate(self.central_bank.state.policy_rate)

        # 2. 世帯の預金申請を収集
        from src.environment.markets.financial_market import DepositRequest, LoanRequest

        deposit_requests = []
        for household in self.households:
            # 余剰現金がある場合に預金（月収の2ヶ月分以上の現金）
            if household.profile.cash > household.profile.monthly_income * 2.0:
                surplus = household.profile.cash - household.profile.monthly_income * 2.0
                deposit_amount = surplus * 0.5  # 余剰の50%を預金

                if deposit_amount > 100.0:  # 最低預金額
                    deposit_requests.append(
                        DepositRequest(
                            household_id=household.profile.id,
                            amount=deposit_amount
                        )
                    )

        # 3. 企業の借入申請を収集
        loan_requests = []
        for firm in self.firms:
            # 月次賃金総額を計算
            num_employees = len(firm.profile.employees)
            monthly_wage_bill = num_employees * firm.profile.wage_offered if num_employees > 0 else 0.0

            # 運転資金が不足している場合に借入（賃金総額の2ヶ月分未満）
            required_cash = monthly_wage_bill * 2.0
            if firm.profile.cash < required_cash and monthly_wage_bill > 0:
                loan_amount = monthly_wage_bill * 3.0  # 賃金総額の3ヶ月分を借入

                loan_requests.append(
                    LoanRequest(
                        firm_id=firm.profile.id,
                        amount=loan_amount,
                        purpose="working_capital"
                    )
                )

        # 4. 金融市場で処理
        deposit_transactions = self.financial_market.process_deposits(deposit_requests)
        loan_transactions = self.financial_market.process_loans(loan_requests)

        # 5. 預金結果を反映
        for txn in deposit_transactions:
            for household in self.households:
                if household.profile.id == txn.agent_id:
                    household.profile.cash -= txn.amount
                    household.profile.savings += txn.amount
                    break

        # 6. 借入結果を反映
        for txn in loan_transactions:
            for firm in self.firms:
                if firm.profile.id == txn.agent_id:
                    firm.profile.cash += txn.amount
                    firm.profile.debt += txn.amount
                    break

        logger.info(
            f"Financial: {len(deposit_transactions)} deposits (${sum(t.amount for t in deposit_transactions):.2f}), "
            f"{len(loan_transactions)} loans (${sum(t.amount for t in loan_transactions):.2f})"
        )

    def _calculate_indicators(self) -> dict[str, float]:
        """
        マクロ経済指標を計算

        Returns:
            指標の辞書
        """
        # 家計所得の集計
        if self.households:
            household_incomes = [
                getattr(h.profile, "monthly_income", 50000.0) for h in self.households
            ]
        else:
            household_incomes = []

        # GDP計算（簡略版）
        total_consumption = sum(
            getattr(h, "consumption", 5000.0) for h in self.households
        )
        total_investment = sum(getattr(f, "investment", 10000.0) for f in self.firms)
        government_spending = (
            getattr(self.government.state, "expenditure", 0.0)
            if self.government
            else 0.0
        )

        gdp = total_consumption + total_investment + government_spending

        # インフレ率計算（前期との比較）
        if len(self.state.history.get("gdp", [])) > 0:
            prev_gdp = self.state.history["gdp"][-1]
            if prev_gdp > 0:
                inflation = (gdp - prev_gdp) / prev_gdp
            else:
                inflation = 0.0
        else:
            inflation = 0.0

        # 失業率計算
        total_labor_force = len(self.households)
        if total_labor_force > 0:
            employed = sum(
                1
                for h in self.households
                if getattr(h.profile, "employment_status", "unemployed") == "employed"
            )
            unemployment_rate = (total_labor_force - employed) / total_labor_force
        else:
            unemployment_rate = 0.0

        # Gini係数
        if household_incomes:
            gini = MacroeconomicIndicators.calculate_gini_coefficient(household_incomes)
        else:
            gini = 0.0

        # 政府の状態更新
        if self.government and self.government.state:
            self.government.state.gdp = gdp
            self.government.state.inflation_rate = inflation
            self.government.state.unemployment_rate = unemployment_rate
            self.government.state.gini_coefficient = gini

        # 中央銀行の状態更新
        policy_rate = (
            self.central_bank.state.policy_rate
            if self.central_bank and self.central_bank.state
            else 0.02
        )

        # 実質GDPの計算
        real_gdp = gdp  # デフォルトは名目GDPと同じ

        # 価格データから価格指数を計算
        current_prices = self.goods_market.get_market_prices()

        if current_prices:
            # ステップ0で基準年価格を保存
            if self.base_year_prices is None:
                self.base_year_prices = current_prices.copy()

            # 価格指数を計算（基準年=100）
            if self.base_year_prices:
                # 共通の財IDのみで計算
                common_goods = set(current_prices.keys()) & set(self.base_year_prices.keys())

                if common_goods:
                    # 平均価格比で価格指数を計算
                    current_avg = sum(current_prices[g] for g in common_goods) / len(common_goods)
                    base_avg = sum(self.base_year_prices[g] for g in common_goods) / len(common_goods)

                    if base_avg > 0:
                        price_index = (current_avg / base_avg) * 100.0

                        # 実質GDP = 名目GDP / (価格指数 / 100)
                        real_gdp = gdp / (price_index / 100.0)

        return {
            "gdp": gdp,
            "real_gdp": real_gdp,
            "inflation": inflation,
            "unemployment_rate": unemployment_rate,
            "gini": gini,
            "policy_rate": policy_rate,
            "num_households": len(self.households),
            "num_firms": len(self.firms),
        }

    def _record_history(self, indicators: dict[str, float]):
        """
        指標を履歴に記録

        Args:
            indicators: 指標の辞書
        """
        for key, value in indicators.items():
            if key in self.state.history:
                self.state.history[key].append(value)

        # 価格・需要データを記録（財市場から取得）
        market_prices = self.goods_market.get_market_prices()
        market_demands = self.goods_market.get_market_demands()

        for good_id, price in market_prices.items():
            if good_id not in self.state.history["prices"]:
                self.state.history["prices"][good_id] = []
            self.state.history["prices"][good_id].append(price)

        for good_id, demand in market_demands.items():
            if good_id not in self.state.history["demands"]:
                self.state.history["demands"][good_id] = []
            self.state.history["demands"][good_id].append(demand)

        # 食料支出比率を計算して記録
        food_expenditure_ratios = []
        for household in self.households:
            total_spending = getattr(household, 'total_spending', 0.0)
            food_spending = getattr(household, 'food_spending', 0.0)

            if total_spending > 0:
                ratio = food_spending / total_spending
                food_expenditure_ratios.append(ratio)

        # 平均食料支出比率を記録
        if food_expenditure_ratios:
            avg_ratio = sum(food_expenditure_ratios) / len(food_expenditure_ratios)
            self.state.history["food_expenditure_ratios"].append(avg_ratio)
        else:
            # 取引がない場合は0を記録
            self.state.history["food_expenditure_ratios"].append(0.0)

        # 次のステップのために支出をリセット
        for household in self.households:
            household.food_spending = 0.0
            household.total_spending = 0.0

    def save_state(self, filepath: str | Path):
        """
        シミュレーション状態を保存

        Args:
            filepath: 保存先ファイルパス
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        state_dict = self.state.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"State saved to {filepath}")

    def load_state(self, filepath: str | Path):
        """
        シミュレーション状態を読み込み

        Args:
            filepath: 読み込むファイルパス
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")

        with open(filepath, encoding="utf-8") as f:
            state_dict = json.load(f)

        # 状態の復元
        self.state.step = state_dict["step"]
        self.state.phase = state_dict["phase"]

        # 家計の復元
        self.state.households = [
            HouseholdProfile.from_dict(h) for h in state_dict["households"]
        ]

        # 企業の復元
        self.state.firms = [FirmProfile.from_dict(f) for f in state_dict["firms"]]

        # 政府・中央銀行の復元
        if state_dict["government"]:
            self.state.government = GovernmentState(**state_dict["government"])

        if state_dict["central_bank"]:
            self.state.central_bank = CentralBankState(**state_dict["central_bank"])

        # 市場の復元
        self.state.market = MarketState(**state_dict["market"])

        # 履歴の復元
        self.state.history = state_dict["history"]

        logger.info(f"State loaded from {filepath}")

    def get_indicators(self) -> dict[str, float]:
        """
        現在のマクロ経済指標を取得

        Returns:
            指標の辞書
        """
        return self._calculate_indicators()

    def get_metrics(self) -> dict[str, float]:
        """
        現在のマクロ経済指標を取得（get_indicators()のエイリアス）

        Returns:
            指標の辞書
        """
        indicators = self._calculate_indicators()

        # スクリプトが期待する追加のメトリクス
        if self.households:
            household_incomes = [
                getattr(h.profile, "monthly_income", 50000.0) for h in self.households
            ]
            indicators["average_income"] = sum(household_incomes) / len(
                household_incomes
            )
        else:
            indicators["average_income"] = 0.0

        indicators["total_consumption"] = sum(
            getattr(h, "consumption", 5000.0) for h in self.households
        )
        indicators["total_investment"] = sum(
            getattr(f, "investment", 10000.0) for f in self.firms
        )
        indicators["vacancy_rate"] = (
            getattr(self.state.market, "vacancy_rate", 0.03)
            if self.state.market
            else 0.03
        )
        indicators["government_spending"] = (
            getattr(self.government.state, "expenditure", 0.0)
            if self.government and self.government.state
            else 0.0
        )
        indicators["tax_revenue"] = (
            getattr(self.government.state, "tax_revenue", 0.0)
            if self.government and self.government.state
            else 0.0
        )

        return indicators

    def save_results(self, output_dir: str | Path):
        """
        シミュレーション結果を保存

        Args:
            output_dir: 出力ディレクトリパス
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 結果の構築
        results = {
            "history": self.state.history,
            "metadata": {
                "steps": self.state.step,
                "households": len(self.state.households),
                "firms": len(self.state.firms),
                "seed": self.config.simulation.random_seed,
                "phase": self.state.phase,
            },
        }

        # results.jsonの保存
        results_file = output_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {results_file}")

        # サマリーの保存
        if self.state.history.get("gdp"):
            summary = {
                "final_gdp": self.state.history["gdp"][-1],
                "final_unemployment": self.state.history.get("unemployment", [0])[-1],
                "final_inflation": self.state.history.get("inflation", [0])[-1],
                "final_gini": self.state.history.get("gini", [0])[-1],
                "avg_gdp": sum(self.state.history["gdp"])
                / len(self.state.history["gdp"]),
                "steps": self.state.step,
            }

            summary_file = output_dir / "summary.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"Summary saved to {summary_file}")

    def run(self, steps: int) -> list[dict[str, float]]:
        """
        複数ステップを実行

        Args:
            steps: 実行するステップ数

        Returns:
            各ステップの指標のリスト
        """
        results = []

        for _ in range(steps):
            indicators = self.step()
            results.append(indicators)

        return results

    def reset(self):
        """シミュレーションをリセット"""
        self._initialize_state()
        logger.info("Simulation reset")

    def get_summary(self) -> dict[str, any]:
        """
        シミュレーションサマリーを取得

        Returns:
            サマリー情報
        """
        return {
            "step": self.state.step,
            "phase": self.state.phase,
            "num_households": len(self.state.households),
            "num_firms": len(self.state.firms),
            "current_indicators": self.get_indicators(),
            "history_length": len(self.state.history.get("gdp", [])),
        }

    def add_households(self, count: int):
        """
        新規世帯を追加（人口ショック実験用）

        Args:
            count: 追加する世帯数
        """
        max_households = self.config.agents.households.max
        current_households = len(self.households)

        # 上限チェック
        if current_households >= max_households:
            logger.warning(
                f"Cannot add households: already at maximum ({max_households})"
            )
            return

        # 実際に追加する数（上限を超えない）
        actual_count = min(count, max_households - current_households)

        if actual_count > 0:
            # 新規世帯を生成
            generator = HouseholdProfileGenerator(
                random_seed=self.config.simulation.random_seed + self.state.step
            )
            new_profiles = generator.generate(count=actual_count)

            # HouseholdAgentを初期化して追加
            for profile in new_profiles:
                new_household = HouseholdAgent(
                    household_id=profile.id,
                    profile=profile,
                    llm_interface=self.llm_interface
                )
                self.households.append(new_household)
                self.state.households.append(profile)

            logger.info(
                f"Added {actual_count} new households "
                f"(total: {len(self.households)}/{max_households})"
            )
