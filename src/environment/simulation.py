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
        api_key = get_api_key("OPENAI_API_KEY")
        self.llm_interface = LLMInterface(
            api_key=api_key,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )

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

        # 前期の価格指数（インフレ率計算用）
        self.prev_price_index = None

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
                    profile=HouseholdProfile.from_dict(profile),
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
                list(templates.items()), k=num_initial_firms
            )

            # 企業エージェントを生成
            self.firms = []
            city_center = (50, 50)  # デフォルト都市中心

            for i, (_firm_id, template) in enumerate(selected_templates):
                # プロファイル生成
                profile = FirmTemplateLoader.create_firm_profile(
                    firm_id=str(i + 1),  # 連番ID
                    template=template,
                    location=city_center,
                )

                # エージェント初期化
                firm_agent = FirmAgent(
                    profile=profile, llm_interface=self.llm_interface
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

        # Phase 6.6: 全世帯のmonthly_incomeをリセット（UBI累積バグ修正）
        # 理由: 失業者のmonthly_incomeが累積せず、毎ステップ正しくUBI500のみになるようにする
        for household in self.households:
            household.profile.monthly_income = 0.0

        # 0. 賃金支払い（Phase 9.9.3: 毎月の賃金支払い処理）
        total_wages_paid = 0.0
        for firm in self.firms:
            for employee_id in firm.profile.employees:
                # 従業員を検索
                for household in self.households:
                    if household.profile.id == employee_id:
                        # 賃金支払い
                        wage = firm.profile.wage_offered
                        firm.profile.cash -= wage
                        household.profile.cash += wage
                        household.profile.monthly_income = wage
                        total_wages_paid += wage
                        break

        if total_wages_paid > 0:
            logger.info(
                f"Wage payments: ${total_wages_paid:.2f} paid to {sum(len(f.profile.employees) for f in self.firms)} employees"
            )

        # 企業の投資指標を0で初期化（LLM決定で上書きされる）
        for firm in self.firms:
            firm.investment = 0.0

        # 1. 企業が生産して出品
        listings = []
        for firm in self.firms:
            # 生産能力を計算（スキルマッチング考慮）
            capacity = firm.calculate_production_capacity(self.households)

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
                    price=firm.profile.price,
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
                        max_price=target_listing.price * 1.2,  # 20%まで高く払える
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
                    if not hasattr(household, "consumption"):
                        household.consumption = 0.0
                    household.consumption += txn.total_value
                    total_consumption += txn.total_value

                    # 食料支出と総支出を追跡
                    if not hasattr(household, "food_spending"):
                        household.food_spending = 0.0
                    if not hasattr(household, "total_spending"):
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
                tax = self.government.collect_income_tax(
                    household.profile.monthly_income
                )
                total_income_tax += tax
                # 世帯の現金から税金を差し引く
                household.profile.cash = max(0.0, household.profile.cash - tax)

        # 2. VAT徴収（取引総額から）
        total_vat = 0.0
        total_transactions = sum(
            getattr(h, "consumption", 0.0) for h in self.households
        )
        if total_transactions > 0:
            total_vat = self.government.collect_vat(total_transactions)

        # 3. 政府の税収を更新
        self.government.state.tax_revenue = total_income_tax + total_vat

        # 4. UBI配布（Phase 6.2: 設定ファイルの固定値を使用）
        ubi_expenditure = 0.0
        if self.government.state.ubi_enabled:
            # UBI額は設定ファイルの値で固定（LLMによる変更を無視）
            fixed_ubi_amount = self.config.economy.welfare.ubi_amount
            ubi_expenditure = fixed_ubi_amount * len(self.households)

            # 各世帯にUBIを付与
            for household in self.households:
                household.profile.monthly_income += fixed_ubi_amount

        # 5. 失業給付（Phase 9.9.4: Enum対応）
        from src.models.data_models import EmploymentStatus

        unemployment_expenditure = 0.0
        for household in self.households:
            if household.profile.employment_status == EmploymentStatus.UNEMPLOYED:
                # 失業給付（前職賃金の50%、簡略版では月収の50%）
                benefit = self.government.calculate_unemployment_benefit(
                    household.profile.monthly_income,
                    months_unemployed=1,  # 簡略版
                )
                unemployment_expenditure += benefit
                household.profile.monthly_income += benefit

        # 6. 企業配当（純利益の10%）を世帯に直接配分
        total_dividends = 0.0
        for firm in self.firms:
            # 純利益 = 売上 - コスト（賃金）
            # 売上 = 当月の販売額
            revenue = firm.profile.sales_quantity * firm.profile.price

            # 賃金コスト = 従業員数 × 賃金
            num_employees = len(firm.profile.employees)
            wage_cost = num_employees * firm.profile.wage_offered

            # 純利益
            net_profit = revenue - wage_cost

            # 配当 = 純利益の10%（ただし、純利益がプラスの場合のみ）
            if net_profit > 0:
                dividend = net_profit * 0.1
                firm.profile.cash -= dividend
                total_dividends += dividend

        # 配当を全世帯に均等配分（株主として）
        if total_dividends > 0 and self.households:
            dividend_per_household = total_dividends / len(self.households)
            for household in self.households:
                household.profile.cash += dividend_per_household

        # 7. 政府支出を更新（配当は含めない）
        self.government.state.expenditure = ubi_expenditure + unemployment_expenditure

        # 8. 政府準備金を更新
        budget_balance = (
            self.government.state.tax_revenue - self.government.state.expenditure
        )
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
                        llm_interface=self.llm_interface,
                    )
                    self.households.append(new_household)
                    self.state.households.append(profile)

                logger.info(
                    f"Metabolic: Added {new_count} new households (total: {len(self.households)})"
                )

    def _revision_stage(self):
        """
        Stage 4: 意思決定ステージ（LLM版）

        エージェントがLLMを使用して意思決定を行う
        """
        logger.info("Revision Stage: LLM-based decision making")

        # 1. 世帯エージェントの意思決定（全世帯）
        logger.debug(f"Processing {len(self.households)} household decisions...")
        for i, household in enumerate(self.households):
            # 観察情報を構築
            observation = self._build_household_observation(household)

            # LLMで意思決定（Phase 10.2: 決定頻度管理は将来実装）
            try:
                decision = household.decide_action(observation, self.state.step)
                # 決定を実行
                self._execute_household_decision(household, decision)
            except Exception as e:
                logger.warning(f"Household {household.profile.id} decision failed: {e}")

        logger.info(f"Completed {len(self.households)} household decisions")

        # 2. 企業エージェントの意思決定（全企業）
        logger.debug(f"Processing {len(self.firms)} firm decisions...")
        for i, firm in enumerate(self.firms):
            # 観察情報を構築
            observation = self._build_firm_observation(firm)

            # LLMで意思決定
            try:
                decision = firm.decide_action(observation, self.state.step)
                # 決定を実行
                self._execute_firm_decision(firm, decision)
            except Exception as e:
                logger.warning(f"Firm {firm.profile.id} decision failed: {e}")

        logger.info(f"Completed {len(self.firms)} firm decisions")

        # 3. 政府エージェントの意思決定（3ステップごと）
        if self.state.step % 3 == 0:
            logger.debug("Processing government decision...")
            observation = self._build_government_observation()
            try:
                decision = self.government.decide_action(observation, self.state.step)
                self._execute_government_decision(decision)
                logger.info("Completed government decision")
            except Exception as e:
                logger.warning(f"Government decision failed: {e}")

        # 4. 中央銀行エージェントの意思決定（毎ステップ）
        logger.debug("Processing central bank decision...")
        observation = self._build_central_bank_observation()
        try:
            decision = self.central_bank.decide_action(observation, self.state.step)
            self._execute_central_bank_decision(decision)
            logger.info("Completed central bank decision")
        except Exception as e:
            logger.warning(f"Central bank decision failed: {e}")

        # 5. 労働市場マッチング（既存ロジックを維持）
        logger.debug("Processing labor market matching...")

        # 求人を収集
        job_postings = []
        for firm in self.firms:
            if firm.profile.job_openings > 0:
                posting = JobPosting(
                    firm_id=firm.profile.id,
                    num_openings=firm.profile.job_openings,
                    wage_offered=firm.profile.wage_offered,
                    skill_requirements=firm.profile.skill_requirements,
                    location=firm.profile.location,
                )
                job_postings.append(posting)

        # 求職者を収集（失業者のみ）
        from src.models.data_models import EmploymentStatus

        job_seekers = []
        for household in self.households:
            if household.profile.employment_status == EmploymentStatus.UNEMPLOYED:
                # 最低賃金は月収の80%（簡略版）
                reservation_wage = household.profile.monthly_income * 0.8
                if reservation_wage < 1000:  # 最低希望賃金
                    reservation_wage = 1000

                seeker = JobSeeker(
                    household_id=household.profile.id,
                    skills=household.profile.skills,
                    reservation_wage=reservation_wage,
                    location=household.profile.location,
                    currently_employed=False,
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
                        household.profile.employment_status = EmploymentStatus.EMPLOYED
                        household.profile.monthly_income = match.wage
                        household.profile.employer_id = match.firm_id
                        household.profile.wage = match.wage
                        break

            # Phase 7.7: 拒否統計をログ出力して低マッチング率の原因を特定
            labor_stats = self.labor_market.get_statistics()
            logger.info(
                f"Labor market: {len(matches)} matches from {len(job_postings)} postings and {len(job_seekers)} seekers"
            )
            logger.info(
                f"Labor market stats: match_rate={labor_stats['match_rate']:.2%}, "
                f"rejected_by_wage={labor_stats['rejected_by_wage']}, "
                f"rejected_by_probability={labor_stats['rejected_by_probability']}, "
                f"rejected_by_distance={labor_stats['rejected_by_distance']}"
            )
        else:
            logger.info(
                f"Labor market: No matching ({len(job_postings)} postings, {len(job_seekers)} seekers)"
            )

        # 6. 金融市場統合
        self._financial_stage()

    def _financial_stage(self):
        """
        金融市場統合

        世帯の預金と企業の借入を処理
        """
        logger.debug("Financial Stage")

        # 1. 政策金利の更新
        if self.central_bank and self.central_bank.state:
            self.financial_market.update_policy_rate(
                self.central_bank.state.policy_rate
            )

        # 2. 世帯の預金申請を収集
        from src.environment.markets.financial_market import DepositRequest, LoanRequest

        deposit_requests = []
        for household in self.households:
            # 余剰現金がある場合に預金（月収の2ヶ月分以上の現金）
            if household.profile.cash > household.profile.monthly_income * 2.0:
                surplus = (
                    household.profile.cash - household.profile.monthly_income * 2.0
                )
                deposit_amount = surplus * 0.5  # 余剰の50%を預金

                if deposit_amount > 100.0:  # 最低預金額
                    deposit_requests.append(
                        DepositRequest(
                            household_id=household.profile.id, amount=deposit_amount
                        )
                    )

        # 3. 企業の借入申請を収集
        loan_requests = []
        for firm in self.firms:
            # 月次賃金総額を計算
            num_employees = len(firm.profile.employees)
            monthly_wage_bill = (
                num_employees * firm.profile.wage_offered if num_employees > 0 else 0.0
            )

            # 運転資金が不足している場合に借入（賃金総額の2ヶ月分未満）
            required_cash = monthly_wage_bill * 2.0
            if firm.profile.cash < required_cash and monthly_wage_bill > 0:
                loan_amount = monthly_wage_bill * 3.0  # 賃金総額の3ヶ月分を借入

                loan_requests.append(
                    LoanRequest(
                        firm_id=firm.profile.id,
                        amount=loan_amount,
                        purpose="working_capital",
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

    # ========== LLM意思決定用: 観察情報構築メソッド ==========

    def _build_household_observation(self, household: HouseholdAgent) -> dict[str, any]:
        """
        世帯エージェント用の観察情報を構築

        Args:
            household: 世帯エージェント

        Returns:
            観察情報の辞書
        """
        # 市場価格情報（財市場）
        market_prices = self.goods_market.get_market_prices()
        avg_price = sum(market_prices.values()) / len(market_prices) if market_prices else 100.0

        # 求人情報（労働市場）
        job_openings_count = sum(f.profile.job_openings for f in self.firms)
        avg_wage = sum(f.profile.wage_offered for f in self.firms if f.profile.job_openings > 0) / max(1, sum(1 for f in self.firms if f.profile.job_openings > 0))

        # マクロ経済指標（prev_price_indexを更新しない）
        current_indicators = self._calculate_indicators(update_prev_price_index=False)

        observation = {
            "current_step": self.state.step,
            "phase": self.state.phase,
            "market_prices": {
                "average_price": avg_price,
                "price_range": {"min": min(market_prices.values()) if market_prices else 50.0, "max": max(market_prices.values()) if market_prices else 150.0},
            },
            "labor_market": {
                "job_openings": job_openings_count,
                "average_wage": avg_wage,
                "unemployment_rate": current_indicators.get("unemployment_rate", 0.0),
            },
            "macro_indicators": {
                "gdp": current_indicators.get("gdp", 0.0),
                "inflation": current_indicators.get("inflation", 0.0),
                "gini": current_indicators.get("gini", 0.0),
            },
            "personal_status": {
                "cash": household.profile.cash,
                "monthly_income": household.profile.monthly_income,
                "employment_status": household.profile.employment_status.value if hasattr(household.profile.employment_status, "value") else household.profile.employment_status,
                "employer_id": household.profile.employer_id,
            },
        }

        return observation

    def _build_firm_observation(self, firm: FirmAgent) -> dict[str, any]:
        """
        企業エージェント用の観察情報を構築

        Args:
            firm: 企業エージェント

        Returns:
            観察情報の辞書
        """
        # 市場価格（競合他社）
        market_prices = self.goods_market.get_market_prices()
        competitors_prices = [p for good_id, p in market_prices.items() if good_id != firm.profile.goods_type]
        avg_competitor_price = sum(competitors_prices) / len(competitors_prices) if competitors_prices else firm.profile.price

        # 労働市場状況
        from src.models.data_models import EmploymentStatus

        job_seekers_count = sum(1 for h in self.households if h.profile.employment_status == EmploymentStatus.UNEMPLOYED)
        avg_market_wage = sum(f.profile.wage_offered for f in self.firms) / len(self.firms) if self.firms else 2000.0

        # マクロ経済指標（prev_price_indexを更新しない）
        current_indicators = self._calculate_indicators(update_prev_price_index=False)

        observation = {
            "current_step": self.state.step,
            "phase": self.state.phase,
            "firm_status": {
                "cash": firm.profile.cash,
                "debt": firm.profile.debt,
                "capital": firm.profile.capital,
                "inventory": firm.profile.inventory,
                "last_production": firm.profile.production_quantity,
                "last_sales": firm.profile.sales_quantity,
                "current_price": firm.profile.price,
                "num_employees": len(firm.profile.employees),
                "wage_offered": firm.profile.wage_offered,
                "job_openings": firm.profile.job_openings,
            },
            "market_conditions": {
                "average_competitor_price": avg_competitor_price,
                "own_goods_type": firm.profile.goods_type,
            },
            "labor_market": {
                "job_seekers": job_seekers_count,
                "average_market_wage": avg_market_wage,
            },
            "macro_indicators": {
                "gdp": current_indicators.get("gdp", 0.0),
                "inflation": current_indicators.get("inflation", 0.0),
                "unemployment_rate": current_indicators.get("unemployment_rate", 0.0),
            },
        }

        return observation

    def _build_government_observation(self) -> dict[str, any]:
        """
        政府エージェント用の観察情報を構築

        Returns:
            観察情報の辞書
        """
        # マクロ経済指標（すべて、prev_price_indexを更新しない）
        current_indicators = self._calculate_indicators(update_prev_price_index=False)

        # 税収・支出・準備金
        budget_balance = self.government.state.tax_revenue - self.government.state.expenditure

        # GDP成長率（前期比）
        gdp_growth = 0.0
        if len(self.state.history["gdp"]) >= 2:
            prev_gdp = self.state.history["gdp"][-1]
            current_gdp = current_indicators.get("gdp", 0.0)
            if prev_gdp > 0:
                gdp_growth = (current_gdp - prev_gdp) / prev_gdp

        observation = {
            "current_step": self.state.step,
            "phase": self.state.phase,
            "fiscal_status": {
                "reserves": self.government.state.reserves,
                "tax_revenue": self.government.state.tax_revenue,
                "expenditure": self.government.state.expenditure,
                "budget_balance": budget_balance,
            },
            "tax_policy": {
                "vat_rate": self.government.state.vat_rate,
                "income_tax_brackets": self.government.state.income_tax_brackets,
            },
            "welfare_policy": {
                "ubi_enabled": self.government.state.ubi_enabled,
                "ubi_amount": self.government.state.ubi_amount,
                "unemployment_benefit_rate": self.government.state.unemployment_benefit_rate,
            },
            "macro_indicators": {
                "gdp": current_indicators.get("gdp", 0.0),
                "real_gdp": current_indicators.get("real_gdp", 0.0),
                "gdp_growth": gdp_growth,
                "inflation": current_indicators.get("inflation", 0.0),
                "unemployment_rate": current_indicators.get("unemployment_rate", 0.0),
                "gini": current_indicators.get("gini", 0.0),
            },
        }

        return observation

    def _build_central_bank_observation(self) -> dict[str, any]:
        """
        中央銀行エージェント用の観察情報を構築

        Returns:
            観察情報の辞書
        """
        # マクロ経済指標（prev_price_indexを更新しない）
        current_indicators = self._calculate_indicators(update_prev_price_index=False)

        # 潜在GDP（簡略版: 過去平均の1.02倍）
        if len(self.state.history["gdp"]) >= 3:
            recent_gdp = self.state.history["gdp"][-3:]
            potential_gdp = sum(recent_gdp) / len(recent_gdp) * 1.02
        else:
            potential_gdp = current_indicators.get("gdp", 100000.0) * 1.02

        # 産出ギャップ
        current_gdp = current_indicators.get("gdp", 100000.0)
        output_gap = (current_gdp - potential_gdp) / potential_gdp if potential_gdp > 0 else 0.0

        # 金融システムの健全性
        loan_to_deposit_ratio = 0.0
        if self.central_bank.state.total_deposits > 0:
            loan_to_deposit_ratio = self.central_bank.state.total_loans / self.central_bank.state.total_deposits

        # 求人率（ベバリッジ曲線用）
        total_jobs = sum(f.profile.job_openings for f in self.firms)
        vacancy_rate = total_jobs / len(self.households) if self.households else 0.0

        observation = {
            "current_step": self.state.step,
            "phase": self.state.phase,
            "monetary_policy": {
                "current_policy_rate": self.central_bank.state.policy_rate,
                "natural_rate": self.central_bank.state.natural_rate,
                "inflation_target": self.central_bank.state.inflation_target,
            },
            "macro_indicators": {
                "gdp": current_gdp,
                "potential_gdp": potential_gdp,
                "output_gap": output_gap,
                "inflation": current_indicators.get("inflation", 0.0),
                "unemployment_rate": current_indicators.get("unemployment_rate", 0.0),
                "vacancy_rate": vacancy_rate,
            },
            "financial_system": {
                "total_deposits": self.central_bank.state.total_deposits,
                "total_loans": self.central_bank.state.total_loans,
                "loan_to_deposit_ratio": loan_to_deposit_ratio,
            },
        }

        return observation

    # ========== LLM意思決定用: 決定実行メソッド ==========

    def _execute_household_decision(self, household: HouseholdAgent, decision: dict[str, any]):
        """
        世帯エージェントのLLM決定を実行

        Args:
            household: 世帯エージェント
            decision: LLMの決定結果
        """
        function_name = decision.get("function_name")
        arguments = decision.get("arguments", {})

        if function_name == "decide_consumption":
            # 消費決定は次のProduction & Trading Stageで処理されるため、
            # ここでは消費嗜好を更新するのみ
            goods = arguments.get("goods", {})
            logger.debug(f"Household {household.profile.id} decided to consume: {goods}")

        elif function_name == "labor_action":
            # Phase 1.4: 労働市場行動（辞職処理を追加）
            action = arguments.get("action")

            # 辞職処理（雇用中の場合のみ）
            from src.models.data_models import EmploymentStatus

            if action == "resign" and household.profile.employment_status == EmploymentStatus.EMPLOYED:
                # 現在の雇用主から削除
                employer_id = household.profile.employer_id
                for firm in self.firms:
                    if firm.profile.id == employer_id:
                        if household.profile.id in firm.profile.employees:
                            firm.profile.employees.remove(household.profile.id)
                            firm.profile.job_openings += 1  # 求人枠を1つ増やす
                        break

                # 雇用状態を失業に変更
                household.profile.employment_status = EmploymentStatus.UNEMPLOYED
                household.profile.employer_id = None
                household.profile.monthly_income = 0.0
                household.profile.wage = 0.0
                logger.debug(f"Household {household.profile.id} resigned from job")
            else:
                # その他のアクション（求職は自動的に労働市場マッチングで処理）
                logger.debug(f"Household {household.profile.id} labor action: {action}")

        elif function_name == "choose_housing":
            # 住居選択
            location = arguments.get("location")
            if location and len(location) == 2:
                household.profile.location = tuple(location)
                logger.debug(f"Household {household.profile.id} moved to {location}")

        elif function_name == "financial_decision":
            # 金融決定（Phase 7.3.1: ヒューリスティック貯蓄も可能）
            action = arguments.get("action")
            amount = arguments.get("amount", 0.0)

            if action == "save" and household.profile.cash >= amount:
                household.profile.cash -= amount
                household.profile.savings += amount
                logger.debug(f"Household {household.profile.id} saved ${amount:.2f}")
            elif action == "withdraw" and household.profile.savings >= amount:
                household.profile.savings -= amount
                household.profile.cash += amount
                logger.debug(f"Household {household.profile.id} withdrew ${amount:.2f}")

        elif function_name == "modify_needs":
            # 消費嗜好の更新
            preferences = arguments.get("preferences", {})
            if preferences:
                household.profile.consumption_preferences.update(preferences)
                logger.debug(f"Household {household.profile.id} modified preferences")

    def _execute_firm_decision(self, firm: FirmAgent, decision: dict[str, any]):
        """
        企業エージェントのLLM決定を実行

        Args:
            firm: 企業エージェント
            decision: LLMの決定結果
        """
        function_name = decision.get("function_name")
        arguments = decision.get("arguments", {})

        if function_name == "decide_production":
            # 生産量と価格を更新
            target_production = arguments.get("target_production", firm.profile.production_quantity)
            price = arguments.get("price", firm.profile.price)

            # 生産能力チェック
            capacity = firm.calculate_production_capacity(self.households)
            actual_production = min(target_production, capacity)

            # Phase 1.1: 需給バランスに応じた価格調整
            # 在庫と販売量の比率から需給バランスを判定
            if firm.profile.sales_quantity > 0:
                inventory_sales_ratio = firm.profile.inventory / firm.profile.sales_quantity
            else:
                inventory_sales_ratio = 1.0  # デフォルト

            # 在庫過剰（販売量の2倍以上）→ 価格を5-10%下げる
            if inventory_sales_ratio > 2.0:
                price_adjustment = 0.90  # 10%値下げ
                price = price * price_adjustment
                logger.debug(f"Firm {firm.profile.id}: Inventory excess, lowering price by 10%")
            # 在庫不足（販売量の0.5倍以下）→ 価格を5-10%上げる
            elif inventory_sales_ratio < 0.5 and firm.profile.inventory < 10.0:
                price_adjustment = 1.10  # 10%値上げ
                price = price * price_adjustment
                logger.debug(f"Firm {firm.profile.id}: Inventory shortage, raising price by 10%")

            # 価格制約: 最低50.0、最高200.0
            price = max(50.0, min(200.0, price))

            firm.profile.production_quantity = actual_production
            firm.profile.price = price

            logger.debug(f"Firm {firm.profile.id} set production={actual_production:.2f}, price=${price:.2f}")

        elif function_name == "labor_decision":
            # 労働市場行動
            action = arguments.get("action")
            wage_offered = arguments.get("wage_offered")
            job_openings = arguments.get("job_openings")
            fire_employee_ids = arguments.get("fire_employee_ids", [])

            if action == "hire":
                # Phase 7.1: 雇用目標を資本規模ベースで計算（分母を25,000に変更）
                # 理由: 従業員数ベースだと従業員が少ない企業は求人を増やせない循環問題が発生
                # 資本規模に応じた適正な雇用目標を設定
                current_employees = len(firm.profile.employees)

                # 雇用目標 = 資本 / 25,000（資本規模に比例）
                # 例: 資本50,000 → 目標2人、資本500,000 → 目標20人
                required_labor = max(1, int(firm.profile.capital / 25000))

                # Phase 7.3: 計算値を優先（LLMが低い値を提案しても、必要人数は確保）
                if job_openings is not None:
                    calculated_openings = max(0, required_labor - current_employees)
                    # LLM決定と計算値の大きい方を採用（求人不足を防ぐ）
                    final_openings = max(job_openings, calculated_openings)
                    firm.profile.job_openings = max(1, final_openings)
                else:
                    # LLMが指定しない場合は計算値を使用
                    firm.profile.job_openings = max(1, required_labor - current_employees)

                if wage_offered:
                    firm.profile.wage_offered = max(1000.0, wage_offered)

                # Phase 4.1診断ログ
                logger.info(
                    f"Firm {firm.profile.id} hiring: capital=${firm.profile.capital:.0f}, "
                    f"employees={current_employees}, required={required_labor}, "
                    f"LLM_openings={job_openings}, final_openings={firm.profile.job_openings}"
                )

            elif action == "fire" and fire_employee_ids:
                # 解雇処理
                from src.models.data_models import EmploymentStatus
                for employee_id in fire_employee_ids:
                    if employee_id in firm.profile.employees:
                        firm.profile.employees.remove(employee_id)
                        # 世帯の雇用状態更新
                        for household in self.households:
                            if household.profile.id == employee_id:
                                household.profile.employment_status = EmploymentStatus.UNEMPLOYED
                                household.profile.employer_id = None
                                household.profile.monthly_income = 0.0
                                household.profile.wage = 0.0
                                break
                logger.debug(f"Firm {firm.profile.id} fired {len(fire_employee_ids)} employees")

            elif action == "adjust_wage" and wage_offered:
                firm.profile.wage_offered = max(1000.0, wage_offered)
                logger.debug(f"Firm {firm.profile.id} adjusted wage to ${wage_offered:.2f}")

        elif function_name == "investment_decision":
            # 投資決定
            action = arguments.get("action")
            amount = arguments.get("amount", 0.0)

            # Phase 1.3: 利益ベースの投資メカニズム強化
            # 月次利益を計算（売上 - 賃金コスト）
            revenue = firm.profile.sales_quantity * firm.profile.price
            num_employees = len(firm.profile.employees)
            wage_cost = num_employees * firm.profile.wage_offered
            monthly_profit = revenue - wage_cost

            # 利益が出ている場合、最低限の資本維持投資を自動実行
            if monthly_profit > 0:
                # LLM決定が投資の場合: 利益の20%を投資
                if action == "invest_capital":
                    # LLM指定額と利益の20%の大きい方を投資
                    auto_investment = monthly_profit * 0.20
                    investment_amount = max(amount, auto_investment)

                    if firm.profile.cash >= investment_amount:
                        firm.profile.cash -= investment_amount
                        firm.profile.capital += investment_amount
                        # investmentフィールドを更新（Phase 9.8の投資指標）
                        firm.investment = investment_amount
                        logger.debug(
                            f"Firm {firm.profile.id} invested ${investment_amount:.2f} in capital "
                            f"(profit: ${monthly_profit:.2f})"
                        )
                # LLM決定が何もしない場合でも、利益の10%を自動投資
                elif action == "do_nothing":
                    auto_investment = monthly_profit * 0.10
                    if firm.profile.cash >= auto_investment:
                        firm.profile.cash -= auto_investment
                        firm.profile.capital += auto_investment
                        firm.investment = auto_investment
                        logger.debug(
                            f"Firm {firm.profile.id} auto-invested ${auto_investment:.2f} "
                            f"(maintenance, profit: ${monthly_profit:.2f})"
                        )

            # 既存の投資ロジック
            if action == "borrow":
                # 借入申請（Financial Stageで処理されるため、ここでは記録のみ）
                logger.debug(f"Firm {firm.profile.id} requested loan: ${amount:.2f}")
            elif action == "invest_capital" and firm.profile.cash >= amount and monthly_profit <= 0:
                # 利益がない場合のみ、LLM指定額をそのまま投資
                firm.profile.cash -= amount
                firm.profile.capital += amount
                firm.investment = amount
                logger.debug(f"Firm {firm.profile.id} invested ${amount:.2f} in capital")
            elif action == "repay_debt" and firm.profile.debt >= amount and firm.profile.cash >= amount:
                # 負債返済
                firm.profile.cash -= amount
                firm.profile.debt -= amount
                logger.debug(f"Firm {firm.profile.id} repaid ${amount:.2f} debt")

        # 全企業に対して、決定内容に関わらず自動投資を実行
        # （investment_decision関数で既に投資済みの場合はスキップ）
        if function_name != "investment_decision" and firm.investment == 0.0:
            # 月次利益を計算
            revenue = firm.profile.sales_quantity * firm.profile.price
            num_employees = len(firm.profile.employees)
            wage_cost = num_employees * firm.profile.wage_offered
            monthly_profit = revenue - wage_cost

            # 利益がある場合、利益の10%を自動投資（資本維持）
            if monthly_profit > 0:
                auto_investment = monthly_profit * 0.10
                if firm.profile.cash >= auto_investment:
                    firm.profile.cash -= auto_investment
                    firm.profile.capital += auto_investment
                    firm.investment = auto_investment
                    logger.debug(
                        f"Firm {firm.profile.id} auto-invested ${auto_investment:.2f} "
                        f"(not called investment_decision, profit: ${monthly_profit:.2f})"
                    )

        # Phase 7.1: 全企業に対して、labor_decisionを呼び出さなかった場合も雇用目標を維持
        # 理由: LLMは3つの関数から1つしか選択できないため、多くの企業がlabor_decision以外を選択
        # 雇用不足の企業は自動的に求人を維持/増加させることで、失業率を健全な範囲に保つ
        if function_name != "labor_decision":
            current_employees = len(firm.profile.employees)
            # Phase 7.1: 分母を25,000に変更（企業の雇用目標を2倍に）
            required_labor = max(1, int(firm.profile.capital / 25000))

            if current_employees < required_labor:
                # 雇用不足の場合、求人を維持/増加
                needed = required_labor - current_employees
                firm.profile.job_openings = max(firm.profile.job_openings, needed)
                logger.debug(
                    f"Firm {firm.profile.id} auto-maintained job openings: "
                    f"capital=${firm.profile.capital:.0f}, employees={current_employees}, "
                    f"required={required_labor}, job_openings={firm.profile.job_openings}"
                )

        # Phase 7.5: 全企業に対して、決定内容に関わらず最終的な求人数チェック
        # 理由: 一部企業がどの決定関数も呼ばない（fallback）ケースで求人が0になる問題を解決
        # どの関数を呼んだかに関係なく、資本規模に応じた最低限の求人を強制的に確保
        current_employees = len(firm.profile.employees)
        required_labor = max(1, int(firm.profile.capital / 25000))

        if current_employees < required_labor:
            # 雇用不足の場合、必要人数を強制的に求人設定
            needed = required_labor - current_employees
            if firm.profile.job_openings < needed:
                firm.profile.job_openings = needed
                logger.info(
                    f"Firm {firm.profile.id} FORCED job openings: "
                    f"capital=${firm.profile.capital:.0f}, employees={current_employees}, "
                    f"required={required_labor}, job_openings={firm.profile.job_openings}"
                )

    def _execute_government_decision(self, decision: dict[str, any]):
        """
        政府エージェントのLLM決定を実行

        Args:
            decision: LLMの決定結果
        """
        function_name = decision.get("function_name")
        arguments = decision.get("arguments", {})

        if function_name == "adjust_tax_policy":
            # 税制調整
            income_tax_adjustment = arguments.get("income_tax_adjustment", 0.0)
            vat_adjustment = arguments.get("vat_adjustment", 0.0)

            # VAT税率調整（±5%以内）
            self.government.state.vat_rate = max(0.0, min(0.5, self.government.state.vat_rate + vat_adjustment))

            # 所得税率調整（全ブラケットに適用、±10%以内）
            if income_tax_adjustment != 0.0:
                new_brackets = []
                for threshold, rate in self.government.state.income_tax_brackets:
                    new_rate = max(0.0, min(0.5, rate + income_tax_adjustment))
                    new_brackets.append((threshold, new_rate))
                self.government.state.income_tax_brackets = new_brackets
                self.government.taxation = self.government.taxation.__class__(brackets=new_brackets)

            logger.debug(f"Government adjusted tax policy: VAT={self.government.state.vat_rate:.3f}")

        elif function_name == "adjust_welfare_policy":
            # 福祉政策調整
            ubi_enabled = arguments.get("ubi_enabled")
            ubi_amount = arguments.get("ubi_amount")
            unemployment_benefit_rate = arguments.get("unemployment_benefit_rate")

            if ubi_enabled is not None:
                self.government.state.ubi_enabled = ubi_enabled
            if ubi_amount is not None:
                self.government.state.ubi_amount = max(0.0, ubi_amount)
            if unemployment_benefit_rate is not None:
                self.government.state.unemployment_benefit_rate = max(0.0, min(1.0, unemployment_benefit_rate))

            logger.debug(f"Government adjusted welfare: UBI={self.government.state.ubi_enabled}, amount=${self.government.state.ubi_amount:.2f}")

        elif function_name == "public_investment":
            # 公共投資
            investment_type = arguments.get("investment_type")
            amount = arguments.get("amount", 0.0)

            if investment_type != "none" and amount > 0 and self.government.state.reserves >= amount:
                self.government.state.reserves -= amount
                self.government.state.expenditure += amount
                logger.debug(f"Government invested ${amount:.2f} in {investment_type}")

        elif function_name == "maintain_policy":
            # 現状維持
            logger.debug("Government maintaining current policy")

    def _execute_central_bank_decision(self, decision: dict[str, any]):
        """
        中央銀行エージェントのLLM決定を実行

        Args:
            decision: LLMの決定結果
        """
        function_name = decision.get("function_name")
        arguments = decision.get("arguments", {})

        if function_name == "set_policy_rate":
            # 政策金利設定
            target_rate = arguments.get("target_rate", self.central_bank.state.policy_rate)
            use_taylor_rule = arguments.get("use_taylor_rule", True)

            if use_taylor_rule:
                # Taylor rule + 金利平滑化
                self.central_bank.update_policy_rate(target_rate, use_smoothing=True)
            else:
                # 直接設定
                self.central_bank.state.policy_rate = max(0.0, target_rate)

            logger.debug(f"Central Bank set policy rate to {self.central_bank.state.policy_rate * 100:.2f}%")

        elif function_name == "adjust_spreads":
            # スプレッド調整
            deposit_spread_change = arguments.get("deposit_spread_change", 0.0)
            loan_spread_change = arguments.get("loan_spread_change", 0.0)

            self.central_bank.state.deposit_rate_spread = max(-0.05, min(0.0, self.central_bank.state.deposit_rate_spread + deposit_spread_change))
            self.central_bank.state.loan_rate_spread = max(0.0, min(0.10, self.central_bank.state.loan_rate_spread + loan_spread_change))

            logger.debug(f"Central Bank adjusted spreads: deposit={self.central_bank.state.deposit_rate_spread:.3f}, loan={self.central_bank.state.loan_rate_spread:.3f}")

        elif function_name == "maintain_policy":
            # 現状維持
            logger.debug("Central Bank maintaining current policy")

    def _calculate_indicators(self, update_prev_price_index: bool = True) -> dict[str, float]:
        """
        マクロ経済指標を計算

        Args:
            update_prev_price_index: 価格指数を次ステップ用に更新するか（observation構築時はFalse）

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
            getattr(h, "consumption", 0.0) for h in self.households
        )
        total_investment = sum(
            getattr(f, "investment", 0.0) for f in self.firms
        )
        government_spending = (
            getattr(self.government.state, "expenditure", 0.0)
            if self.government
            else 0.0
        )

        gdp = total_consumption + total_investment + government_spending

        # インフレ率計算は価格指数計算後に行う（後で計算）
        inflation = 0.0

        # 失業率計算（Phase 9.9.4: Enum対応）
        total_labor_force = len(self.households)
        if total_labor_force > 0:
            from src.models.data_models import EmploymentStatus

            employed = sum(
                1
                for h in self.households
                if h.profile.employment_status == EmploymentStatus.EMPLOYED
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
        logger.info(
            f"[Inflation] Step {self.state.step}: current_prices count = {len(current_prices)}"
        )

        # 基準年価格を設定（価格データがある最初のステップ）
        if self.base_year_prices is None and current_prices:
            self.base_year_prices = current_prices.copy()
            # 初期価格指数を100.0に設定（基準年）
            self.prev_price_index = 100.0
            logger.info(f"Base year prices set with {len(self.base_year_prices)} goods")
            logger.info(f"[Inflation] base_year_prices = {self.base_year_prices}")
            logger.info(f"[Inflation] Initialized prev_price_index = 100.0 (base year)")

        # 価格指数を計算（基準年価格と現在価格の両方がある場合のみ）
        if self.base_year_prices and current_prices:
            # 共通の財IDのみで計算
            common_goods = set(current_prices.keys()) & set(
                self.base_year_prices.keys()
            )
            logger.info(
                f"[Inflation] common_goods = {common_goods} ({len(common_goods)} goods)"
            )

            if common_goods:
                # 平均価格比で価格指数を計算
                current_avg = sum(current_prices[g] for g in common_goods) / len(
                    common_goods
                )
                base_avg = sum(self.base_year_prices[g] for g in common_goods) / len(
                    common_goods
                )
                logger.info(
                    f"[Inflation] current_avg={current_avg:.2f}, base_avg={base_avg:.2f}"
                )

                if base_avg > 0:
                    price_index = (current_avg / base_avg) * 100.0
                    logger.info(
                        f"[Inflation] price_index={price_index:.4f}, prev_price_index={self.prev_price_index}"
                    )

                    # 実質GDP = 名目GDP / (価格指数 / 100)
                    real_gdp = gdp / (price_index / 100.0)

                    # インフレ率を価格指数から計算
                    if self.prev_price_index is not None and self.prev_price_index > 0:
                        inflation = (
                            price_index - self.prev_price_index
                        ) / self.prev_price_index
                        logger.info(
                            f"[Inflation] CALCULATED: inflation={inflation:.6f} ({inflation * 100:.4f}%)"
                        )
                    else:
                        # 初回ステップ（base_year設定時）はインフレ率0
                        inflation = 0.0
                        logger.info("[Inflation] First step: inflation=0.0 (expected)")

                    # 次のステップのために現在の価格指数を保存（メインステップのみ）
                    if update_prev_price_index:
                        self.prev_price_index = price_index
                        logger.info(f"[Inflation] Updated prev_price_index to {price_index:.4f} for next step")
                else:
                    logger.warning(f"[Inflation] base_avg <= 0: {base_avg}")
            else:
                logger.warning(
                    "[Inflation] No common goods between base_year and current prices!"
                )
        else:
            if not self.base_year_prices:
                logger.info("[Inflation] No base_year_prices yet")
            if not current_prices:
                logger.warning("[Inflation] No current_prices available!")

        return {
            "gdp": gdp,
            "real_gdp": real_gdp,
            "inflation": inflation,
            "unemployment_rate": unemployment_rate,
            "gini": gini,
            "policy_rate": policy_rate,
            "num_households": len(self.households),
            "num_firms": len(self.firms),
            "consumption": total_consumption,
            "investment": total_investment,
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

        # 食料支出比率を計算して記録（Engel's Law検証用）
        # 全世帯分を記録（取引がない世帯は0.0）
        food_expenditure_ratios = []
        for household in self.households:
            total_spending = getattr(household, "total_spending", 0.0)
            food_spending = getattr(household, "food_spending", 0.0)

            if total_spending > 0:
                ratio = food_spending / total_spending
            else:
                ratio = 0.0  # 取引がない世帯は0
            food_expenditure_ratios.append(ratio)

        # 世帯ごとの食料支出比率を記録
        self.state.history["food_expenditure_ratios"].append(food_expenditure_ratios)

        # 世帯ごとの所得を記録（Engel's Law検証用）
        household_incomes = [
            getattr(h.profile, "monthly_income", 0.0) for h in self.households
        ]
        self.state.history["household_incomes"].append(household_incomes)

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
        # prev_price_indexを更新しない（step()で既に更新済み）
        return self._calculate_indicators(update_prev_price_index=False)

    def get_metrics(self) -> dict[str, float]:
        """
        現在のマクロ経済指標を取得（get_indicators()のエイリアス）

        Returns:
            指標の辞書
        """
        # prev_price_indexを更新しない（step()で既に更新済み）
        indicators = self._calculate_indicators(update_prev_price_index=False)

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
            getattr(h, "consumption", 0.0) for h in self.households
        )
        indicators["total_investment"] = sum(
            getattr(f, "investment", 0.0) for f in self.firms
        )

        # Vacancy Rate（求人率）を動的計算: 総求人数 / 労働力
        total_job_openings = sum(f.profile.job_openings for f in self.firms)
        total_labor_force = len(self.households) if self.households else 1
        indicators["vacancy_rate"] = total_job_openings / total_labor_force
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
                    llm_interface=self.llm_interface,
                )
                self.households.append(new_household)
                self.state.households.append(profile)

            logger.info(
                f"Added {actual_count} new households "
                f"(total: {len(self.households)}/{max_households})"
            )
