import os
import csv
from CoinAgent import AgentManager, BalanceManager

def main():
    # initial balance 1000
    # agent budget ratio = 0.1
    # range spread = 0.1
    # profit margin = 0.1
    ROOT_DIR = os.path.split(__file__)[0]
    hist_file = ROOT_DIR + "/ETH.csv"
    am_logfile = ROOT_DIR + "/CoinAgent_Output.csv"
    
    bm = BalanceManager()
    am = AgentManager(bm, agents_logfolder = ROOT_DIR)
    am.start_agents_log()
    
    with open(hist_file, newline='') as ftr:
        file_reader = csv.DictReader(ftr)
        with open(am_logfile, 'w', newline='') as ftw:
            file_writer = csv.DictWriter(ftw, fieldnames = am.report_fields)
            file_writer.writeheader()
            for row in file_reader:
                today_price = float(row['Close'].replace(",", ""))
                today_date = row['DATE']
                am.buy_cycle(today_price, today_date)
                am.sell_cycle(today_price, today_date)
                file_writer.writerow(am.status_report(today_price, today_date))
    
    
    am.close_agents_log()
    
    
if __name__ == "__main__":
    main()
    