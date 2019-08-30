import csv
from datetime import date, datetime, timedelta
from bisect import bisect_left
from collections import OrderedDict


class PriceNegativeValueError(Exception):
    
    def __init__(self, price):
        message = "Crypto currency should not have negative value: {}".format(price)
        super().__init__(message)
        
        
class NotEnoughBalanceError(Exception):
    
    def __init__(self, balance, cost):
        message = "The balance {} is insufficient to invest {}".format(balance, cost)
        super().__init__(message)
        
        
class AlreadyInvestedError(Exception):
    
    def __init__(self, agent_range):
        message = "Agent currently invested in range {}".format(agent_range)
        super().__init__(message)
        
        
class NothingToSellError(Exception):
    
    def __init__(self):
        message = "Agent has no crypto coins to sell now"
        super().__init__(message)
        
        
class ProfitMarginNotReached(Exception):
    
    def __init__(self, current_margin, expected_margin):
        message = "Margin {} still lower than expected {}".format(current_margin, expected_margin)
        super().__init__(message)


class BalanceManager():

    def __init__(self, start_balance = 1000):
        self.balance = start_balance

    def topup_balance(self, amount):
        self.balance += amount

    def enough_funds(self, cost):
        if self.balance - cost > 0:
            return True
        else:
            return False

    def invest_budget(self, budget):
        self.balance -= budget


class Agent():

    def __init__(self, name, agent_range, fiat_budget, balance, margin, crypt_budget = 0, invested = False):
        self.name = name
        self.agent_range = "[ {0:.2f} - {1:.2f} ]".format(agent_range[0], agent_range[1])
        self.fiat_budget = fiat_budget # how much agent can invest in one go
        self.crypt_budget = crypt_budget
        self.balance = balance # general balance object
        self.margin = margin # how much percent profit to decide to sell, between 0 and 1
        self.last_invested_price = 0
        self.last_invested_date = None
        self.last_divested_price = 0
        self.last_divested_date = None
        self.cumulative_profits = 0
        self.invested = invested
        self.agent_created = datetime.today()


    def invest(self, price, date = None):
        if self.balance.enough_funds(self.fiat_budget):
            if not self.invested:
                # buy
                self.balance.invest_budget(self.fiat_budget)
                self.crypt_budget = self.fiat_budget / price
                self.last_invested_price = price
                if date:
                    self.last_invested_date = datetime.fromisoformat(date)
                else:
                    self.last_invested_date = datetime.today()
                self.invested = True
            else:
                raise AlreadyInvestedError(self.agent_range)
        else:
            raise NotEnoughBalanceError(self.balance.balance, self.fiat_budget)
                    

    def divest(self, price, date = None):
        if self.invested:
            if ( price / self.last_invested_price  - 1 ) >= self.margin:
                # sell
                self.balance.topup_balance(self.fiat_budget)
                self.cumulative_profits += ( price - self.last_invested_price ) * self.crypt_budget
                self.crypt_budget = 0
                self.invested = False
                self.last_divested_price = price
                if date:
                    self.last_divested_date = datetime.fromisoformat(date)
                else:
                    self.last_divested_date = datetime.today()
            else:
                current_margin = "{0:.3f}".format(( price / self.last_invested_price  - 1 ))
                expected_margin = "{0:.3f}".format(self.margin)
                raise ProfitMarginNotReached(current_margin, expected_margin)
        else:
            raise NothingToSellError()
                

    def report(self, price, action, date = None):
        
        if date:
            report_date = datetime.fromisoformat(date)
        else:
            report_date = datetime.today()
            
        if self.invested:
            status = "invested"
        else:
            status = "idle"
            
        report_data = OrderedDict()
        report_data['AGENT_NAME'] = self.name
        report_data['AGENT_RANGE'] = self.agent_range
        report_data['STATUS'] = status
        report_data['ACTION'] = action
        report_data['ACTION_DATE'] = report_date.strftime("%Y-%m-%d")
        report_data['EURO_BUDGET'] = self.fiat_budget
        report_data['CRYPT_BALANCE'] = self.crypt_budget
        report_data['CRYPT_BALANCE_VALUE'] = self.crypt_budget  * price
        report_data['CURR_PRICE'] = price
        report_data['INVESTED_PRICE'] = self.last_invested_price
        report_data['EUR_BALANCE'] = self.balance.balance
        
        return report_data
    
    
    def _get_report_fields(self):
        report = self.report(0, 'get_report_fields', '2019-01-01')
        return report.keys()


class AgentManager():

    def __init__(self, balance, agent_budget_ratio = 0.1, range_spread = 0.1, invest_margin = 0.1, agents_logfolder = None):
        self.balance = balance
        self.agents_budget = balance.balance * agent_budget_ratio
        self.spread = range_spread
        self.margin = invest_margin
        self.ranges = [0]
        self.ranges.extend(self._populate_ranges())
        self.agents = {}
        if agents_logfolder:
            self.log_file = agents_logfolder + "/Coin_Agents_Log_{}.csv".format(datetime.today().strftime("%Y%d%m-%H%M%S"))
        else:
            self.log_file = None
        self.report_fields = self._get_report_fields()
            
            
    def start_agents_log(self):
        field_names = Agent("dummy", (0, 0), 0, self.balance, 0)._get_report_fields() # create dummy agent just to get agents report fields
        self.agents_log = open(self.log_file, 'w', newline='')
        self.file_writer = csv.DictWriter(self.agents_log, fieldnames=field_names)
        self.file_writer.writeheader()
        
        
    def close_agents_log(self):
        self.agents_log.close()
            

    def _populate_ranges(self, lower_limit = 1, upper_limit = 1000):
        next_bound = lower_limit
        range_list = [ lower_limit ]
        while next_bound < upper_limit:
            next_bound *= (1 + self.spread)
            range_list.append(next_bound)
        return range_list
    

    def _find_closest_lower(self, my_number):
        """
        Assumes my_list is sorted. Returns min closest value to my_number.
        """
        pos = bisect_left(self.ranges, my_number)
        # check if my_number is negative
        if pos == 0:
            raise PriceNegativeValueError(my_number)
        if pos == len(self.ranges):
            # if my_number is higher than upper list bound then add some more values
            new_portion = self._populate_ranges(self.ranges[-1], my_number)
            self.ranges.extend(new_portion[1:])
            return self.ranges[-2]
        return self.ranges[pos - 1]
    
    
    def _find_closest_upper(self, my_number):
        pos = bisect_left(self.ranges, my_number)
        return self.ranges[pos]
    
    
    def buy_cycle(self, price, date = None):
        '''
        only one agent buys at any given price range
        '''
        nearest_bound = self._find_closest_lower(price)
        if nearest_bound not in self.agents.keys():
            # create a new agent
            name = "agent_{}".format(len(self.agents))
            next_upper_bound = self._find_closest_upper(price)
            agent_range = ( nearest_bound, next_upper_bound )
            fiat_budget = self.agents_budget
            balance = self.balance
            margin = self.margin
            agent = Agent(name, agent_range, fiat_budget, balance, margin)
            self.agents[nearest_bound] = agent
        else:
            agent = self.agents[nearest_bound]
        
        act = ""
        try:
            agent.invest(price, date)
        except NotEnoughBalanceError as e:
            act = "no_balance"
        except AlreadyInvestedError as e:
            act = "already_invested"
        else:
            act = "buy"
        finally:
            if self.log_file:
                agent_report = agent.report(price, act, date)
                self.file_writer.writerow(agent_report)
    
    
    def sell_cycle(self, price, date = None):
        for agent in self.agents.values():
            act = ""
            try:
                agent.divest(price)
            except ProfitMarginNotReached:
                act = "not_enough_profit"
            except NothingToSellError:
                act = "no_crypt_bal"
            else:
                act = "sell"
            finally:
                if self.log_file:
                    agent_report = agent.report(price, act, date)
                    self.file_writer.writerow(agent_report)
            
    
    def status_report(self, price, date = None):
        active_agents = 0
        idle_agents = 0
        buys_today = 0
        sells_today = 0
        cryp_balance = 0
        invested_value = 0
        tot_value = 0
        if date:
            today = datetime.fromisoformat(date)
        else:
            today = datetime.today()
        
        for agent in self.agents.values():
            agent_report = agent.report(price, date)
            if agent.invested:
                active_agents += 1
                invested_value += agent.crypt_budget * agent.last_invested_price
            else:
                idle_agents += 1
            
            if agent.last_divested_date:
                if (today.date() - agent.last_divested_date.date()).days == 0:
                    sells_today += 1
            
            if agent.last_invested_date:
                if (today.date() - agent.last_invested_date.date()).days == 0:
                    buys_today += 1
            
            cryp_balance += agent.crypt_budget
            
        cryp_balance_value = cryp_balance * price
        tot_value = self.balance.balance + cryp_balance_value
        status_report = OrderedDict()
        status_report['DATE'] = today.strftime("%Y-%m-%d")
        status_report['PRICE'] = price
        status_report['ACTIVE_AGENTS'] = active_agents
        status_report['IDLE_AGENTS'] = idle_agents
        status_report['BUYS_TODAY'] = buys_today
        status_report['SELLS_TODAY'] = sells_today
        status_report['GLOBAL_BALANCE'] = self.balance.balance
        status_report['CRYP_BALANCE'] = cryp_balance
        status_report['CRYP_BALANCE_VALUE'] = cryp_balance_value
        status_report['TOT_VALUE'] = tot_value
        
        return status_report
    
    
    def _get_report_fields(self):
        report = self.status_report(0, '2019-01-01')
        return report.keys()

