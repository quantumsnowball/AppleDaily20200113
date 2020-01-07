br = breakpoint
import os, argparse
import pandas as pd, matplotlib.pyplot as plt

class Stock:
    def __init__(self, **configs):
        for name,value in configs.items():
            setattr(self, '_'+name, value)
        self._today = self._get_ohlcv(self._ticker).loc[self._start:]
        self._yesterday = self._today.shift(1)
        

    def _get_ohlcv(self, ticker):
        ohlcv = pd.read_csv(f'resources/{ticker}.csv', index_col=0, parse_dates=True)
        return ohlcv

    def _plot_gaps(self, gaps, title=None, desc=None):
        gap_ups, gap_dns = gaps['up'], gaps['dn']
        fig, ax = plt.subplots(1,1, figsize=(12,8))
        ax.set_title(f'{title}\n{desc}')
        self._today['Close'].plot(ax=ax, c='gray')        
        ax.scatter(gap_ups.index, gap_ups, c='green', marker='.', s=150)
        ax.scatter(gap_dns.index, gap_dns, c='red', marker='.', s=150)
        
        dir = f'images/{self._ticker}'
        if not os.path.exists(dir): os.makedirs(dir)
        plt.savefig(f'{dir}/{title}.png')
        # plt.show()

    def find_gaps(self, plot=False):
        width = self._minWidth/100
        ups = self._today['Low'].loc[self._today.Low / self._yesterday.High > 1+width]
        dns = self._today['High'].loc[self._today.High / self._yesterday.Low < 1-width]        
        gaps = {'up': ups, 'dn': dns}
        title = f'All gaps with width more than {width:.1%}'
        desc = (f'{self._ticker}: qFrom {self._today.index[0].date()} to {self._today.index[-1].date()}, {len(self._today)} days, '
                f'total {len(ups)} up gaps and {len(dns)} down gaps')
        print(desc)
        if plot:
            self._plot_gaps(gaps, title=title, desc=desc)
        return gaps

    def find_unfilled_gaps(self, rollD=None, plot=False, **kwargs):
        gaps = self.find_gaps(plot=True, **kwargs)
        ups, dns = gaps['up'], gaps['dn']
        def is_unfilled(gap_date, up=True):
            if up:
                after = self._today['Low'].loc[gap_date:]
                target = self._yesterday.loc[gap_date,'High']
                return target < after.min()
            else:
                after = self._today['High'].loc[gap_date:]
                target = self._yesterday.loc[gap_date,'Low']
                return target > after.max()
        ups_unf = ups.loc[ups.index.map(lambda x: is_unfilled(x, True))]
        dns_unf = dns.loc[dns.index.map(lambda x: is_unfilled(x, False))]
        gaps = {'up': ups_unf, 'dn': dns_unf}
        title = f'All unfilled gaps with width more than {self._minWidth/100:.1%}'
        desc = (f'{self._ticker}: From {self._today.index[0].date()} to {self._today.index[-1].date()}, {len(self._today)} days, '
                f'total {len(ups_unf)} unfilled up gaps and {len(dns_unf)} unfilled down gaps')
        print(desc)
        if plot:
            self._plot_gaps(gaps, title=title, desc=desc)
        return gaps

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-t', '--ticker', type=str, default='^HSI', help='Stock ticker to analyse')
    parser.add_argument('-s', '--start', type=str, default='20000101', help='Start date')
    parser.add_argument('-mW', '--minWidth', type=float, default=.5, help='Min gap width threadhold in %')
    sargs = parser.parse_args()

    stock = Stock(**vars(sargs))
    stock.find_unfilled_gaps(plot=True,)

if __name__ == "__main__":
    main()