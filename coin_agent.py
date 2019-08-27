import csv
from datetime import datetime
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
        self.invested = False

    def invest(self, price, date):
        if self.balance.enough_funds(self.budget):
            if not self.invested:
                # buy
                self.balance.invest_budget(self.fiat_budget)
                self.crypt_budget = self.fiat_budget / price
                self.fiat_budget = 0
                self.last_invested_price = price
                self.last_invested_date = date

    def divest(self, price):
        if self.invested:
            if ( self.last_invested_price / price - 1 ) >= self.margin:
                # sell
                self.fiat_budget = self.crypt_budget * price
                self.balance.topup_balance(self.fiat_budget)
                self.crypt_budget = 0

    def report(self, action, date, price):
        invest_performance = ( price / self.last_invested_price - 1 ) * 100
        report_data = { 'agent_name' : self.name,
                        'action' : action,
                        'date' : date,
                        'euro_balance' : self.fiat_budget,
                        'crypt_balance' : self.crypt_budget,
                        'last_price' : price,
                        'investment_value' : "{0:.2f} %".format(invest_performance),
                        'tot_value' : self.fiat_budget + ( self.crypt_budget * price ) }
        return report_data


class AgentManager():

    def __init__(self, balance, range_spread = 0.2):
        self.balance = balance
        self.spread = range_spread
        self.ranges = [0]
        self.ranges.extend(self._populate_ranges())
        self.agents = {}

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

    def buy_cycle(self, price):
        nearest_bound = self._find_closest(price)
        if nearest_bound not in self.agents.keys():
            # create a new agent
            name = "agent_{}".format(len(self.agents))
            fiat_budget = 200
            balance = self.balance
            margin = self.spread
            agent = Agent(name, fiat_budget, balance, margin)
            self.agents[nearest_bound] = agent
            
    


class CoinAgent():
    
    def __init__(self,
                 buy_price,
                 euro_balance,
                 crypt_balance = 0,
                 margin = 0.2,
                 buy = True,
                 name = None):
        self.buy_price = buy_price
        self.euro_balance = euro_balance
        self.crypt_balance = crypt_balance
        self.profit_margin = margin
        self.buy = buy
        self.name = name
        self.last_purchase_date = None
        self.last_sale_date = None
        self.current_price = None
        
    def evaluate(self, current_price, date):
        self.current_price = current_price
        if self.buy:
            if current_price <= self.buy_price:
                self.crypt_balance = self.euro_balance / current_price
                self.euro_balance = 0
                self.last_purchase_date = date
                self.buy = False
                return self.report('buy', date)
            else:
                return self.report('pass', date)
        else:
            # sell as soon as 20% profit is made
            if current_price >= self.buy_price * ( 1 + self.profit_margin ):
                self.euro_balance = self.crypt_balance * current_price
                self.crypt_balance = 0
                self.last_sale_date = date
                self.buy = True
                return self.report('sell', date)
            else:
                return self.report('pass', date)
        
    def report(self, action, date):
        report_data = { 'agent_name' : self.name,
                       'action' : action,
                       'date' : date,
                       'euro_balance' : self.euro_balance,
                       'crypt_balance' : self.crypt_balance,
                        'last_price' : self.current_price,
                       'tot_value' : self.euro_balance + ( self.crypt_balance * self.current_price ) }
        return report_data



def invest_distr(step, agents_nr, offset, ref_price):
    ''' this function creates a distribution of trigger prices around a price of reference 
    step is the difference in euro between agents buy price triggers,
    offset is a value between 0 and 1 indicating whether the ref price is the lower (0), middle (0.5) or upper (1) limit of the range,
    ref_price is a value that should be set to a sort of average of volatility.'''
    start = step
    stop = step + step * agents_nr
    actual_offset = ref_price - ( stop ) * offset
    return [ x + actual_offset for x in range(start, stop, step) ]

    
        
def main():
    historical_records = "../ETH.csv"
    report_file = "../results.csv"
    euro_balance = 1000
    agents_number = 10
    current_price = 10
    agent_balance = euro_balance / agents_number
    buy_price_distr = invest_distr(100, agents_number, 0, current_price)
    agents_box = []
    for i in range(agents_number):
        agent_name = "agent_{}".format(i)
        agent = CoinAgent(buy_price_distr[i],
                          agent_balance,
                          name = agent_name)
        agents_box.append(agent)
        
    with open(historical_records, newline='') as ftr:
        file_reader = csv.DictReader(ftr)
        with open(report_file, 'w', newline='') as ftw:
            field_names = ['agent_name', 'action', 'date', 'euro_balance', 'crypt_balance', 'last_price', 'tot_value']
            file_writer = csv.DictWriter(ftw, fieldnames=field_names)
            file_writer.writeheader()
            for row in file_reader:
                today_price = float(row['Close'].replace(",", ""))
                today_date = row['DATE']
                for agent in agents_box:
                    results = agent.evaluate(today_price, today_date)
                    if results['action'] != "pass":
                        file_writer.writerow(results)
            # once loop is done, print all agents' report
            for agent in agents_box:
                results = agent.report('exit', today_date)
                file_writer.writerow(results)