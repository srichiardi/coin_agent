from datetime import datetime


class CoinAgent():
    
    def __init__(self,
                 buy_price,
                 euro_balance,
                 crypt_balance = 0,
                 margin = 0.2,
                 buy = True):
        self.buy_price = buy_price
        self.euro_balance = euro_balance
        self.crypt_balance = crypt_balance
        self.profit_margin = margin
        self.buy = buy
        self.last_purchase_date = None
        self.last_sale_date = None
        self.current_price = None
        
    def evaluate(self, current_price, date):
        self.current_price = current_price
        if self.buy:
            if current_price <= self.buy_price:
                self.crypt_balance = self.euro_balance * current_price
                self.euro_balance = 0
                self.last_purchase_date = date
                self.buy = False
                return self.report('buy', date)
            else:
                return self.report('pass', date)
        else:
            delta = (current_price - self.start_price) / self.start_price
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
        report_data = { 'action' : action,
                       'date' : date,
                       'euro_balance' : self.euro_balance,
                       'crypt_balance' : self.crypt_balance,
                       'tot_value' : self.euro_balance + ( self.crypt_balance * self.current_price ) }
        return report_data
        
        
def main():
    historical_records = ""
    euro_balance = 1000
    agents_number = 10
    with open(historical_records) as f:
        for row in f:
            