import csv
from datetime import date, datetime, timedelta
from bisect import bisect_left


class PriceNegativeValueError(Exception):
    
    def __init__(self, price):
        message = "Negative price {}".format(price)
        super().__init__(message)


class BalanceManager():

    def __init__(self):
        self.balance = self.topup_balance(1000)

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

    def __init__(self, name, fiat_budget, balance, margin, crypt_budget = 0):
        self.name = name
        self.fiat_budget = fiat_budget # how much agent can invest
        self.crypt_budget = crypt_budget
        self.balance = balance # general balance object
        self.margin = margin
        self.last_invested_price = 0
        self.last_invested_date = None
        self.last_divested_price = 0
        self.last_divested_date = None
        self.invested = False
        self.agent_created = datetime.today()
        self.first_fiat_budget = fiat_budget

    def invest(self, price, date = None):
        if self.balance.enough_funds(self.budget):
            if not self.invested:
                # buy
                self.balance.invest_budget(self.fiat_budget)
                self.crypt_budget = self.fiat_budget / price
                self.fiat_budget = 0
                self.last_invested_price = price
                if date:
                    self.last_invested_date = datetime.fromisoformat(date)
                else:
                    self.last_invested_date = datetime.today()
                self.invested = True
                return True
            else:
                return False
        else:
            return False
                    

    def divest(self, price, date = None):
        if self.invested:
            if ( self.last_invested_price / price - 1 ) >= self.margin:
                # sell
                self.fiat_budget = self.crypt_budget * price
                self.balance.topup_balance(self.fiat_budget)
                self.crypt_budget = 0
                self.invested = False
                self.last_invested_price = 0
                self.last_divested_price = price
                if date:
                    self.last_divested_date = datetime.fromisoformat(date)
                else:
                    self.last_divested_date = datetime.today()
                return True
            else:
                return False
        else:
            return False
                

    def report(self, price, date = None):
        invest_performance = ( price / self.last_invested_price - 1 ) * 100
        if date:
            report_date = datetime.fromisoformat(date)
        else:
            report_date = datetime.today()
            
        if self.invested:
            invest_performance = ( price / self.last_invested_price - 1 ) * 100
            invest_profit = (price - self.last_invested_price) * self.crypt_budget
            
        report_data = { 'agent_name' : self.name,
                        'date' : report_date.strftime("%Y-%m-%d"),
                        'euro_balance' : self.fiat_budget,
                        'crypt_balance' : self.crypt_budget,
                        'curr_price' : price,
                        'invested_price': self.last_invested_price,
                        'investment_value_str' : "{0:.2f} %".format(invest_performance),
                        'investment_value_pct' : invest_performance,
                        'curr_value' : self.fiat_budget + ( self.crypt_budget * price ),
                        'curr_profit' : invest_profit }
        return report_data


class AgentManager():

    def __init__(self, balance, range_spread = 0.2, agents_logfolder = None):
        self.balance = balance
        self.spread = range_spread
        self.ranges = [0]
        self.ranges.extend(self._populate_ranges())
        self.agents = {}
        if agents_logfolder:
            self.log_file = agents_folder + "/Coin_Agents_Log_{}.csv".format(datetime.today().strftime("%Y%d%m-%H%M%S"))
            

    def _populate_ranges(self, lower_limit = 1, upper_limit = 1000):
        next_bound = lower_limit
        range_list = [ lower_limit ]
        while next_bound < upper_limit:
            next_bound *= (1 + self.spread)
            range_list.append(next_bound)
        return range_list
    

    def _find_closest(self, my_number):
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

    
    def buy_cycle(self, price, date = None):
        nearest_bound = self._find_closest(price)
        if nearest_bound not in self.agents.keys():
            # create a new agent
            name = "agent_{}".format(len(self.agents))
            fiat_budget = 200
            balance = self.balance
            margin = self.spread
            agent = Agent(name, fiat_budget, balance, margin)
            self.agents[nearest_bound] = agent
        
        investor = self.agents[nearest_bound]
        investor.invest(price, date)
    
    
    def sell_cycle(self, price, date = None):
        for agent in self.agents.items():
            agent.divest(price)
            
    
    def status_report(self, price, date = None):
        active_agents = 0
        idle_agents = 0
        tot_invested = 0
        fiat_balance = 0
        cryp_balance = 0
        tot_value = 0
        for agent in self.agents.items():
            agent_report = agent.report(price, date)
            if agent.invested:
                active_agents += 1
            else:
                idle_agents += 1
            tot_invested = 0
            fiat_balance += agent.fiat_budget
            cryp_balance += agent.crypt_budget
            tot_value += agent.fiat_budget + ()

