from datetime import datetime


class CoinAgent():
    
    def __init__(self, start_price, currency, balance, margin = 0.2, purchase_date = datetime.today()):
        self.start_price = start_price
        self.currency = currency
        self.balance = balance
        self.purchase_date = purchase_date
        self.profit_margin = margin
        self.sale_date = None
        self.upward_trend = False
        
    def evaluate(self, current_price, sale_date = datetime.today()):
        delta = (current_price - self.start_price) / self.start_price
        # sell as soon as 20% profit is made
        if delta > self.profit_margin:
            sale = self.balance * current_price
            self.profit = (current_price - self.start_price) * self.balance
            self.balance = 0
            self.sale_date = sale_date
        else:
            return 0
        
    def report(self):
        report_data = { 'purchase_date' : self.purchase_date,
                       'sale_date' : self.sale_date,
                       'invest_days' : '',
                       'profit': self.profit }
        
        
def main():
    historical_records = ""
    euro_balance = 1000
    agents_number = 10
    with open(historical_records) as f:
        for row in f:
            