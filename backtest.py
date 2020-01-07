br = breakpoint
import argparse
import pandas as pd, numpy as np, matplotlib.pyplot as plt

class Strategy:
    def __init__(self, **configs):
        self._config = configs
        for name,value in configs.items():
            setattr(self, '_'+name, value)

    def _get_ohlcv(self, ticker):
        ohlcv = pd.read_csv(f'resources/{ticker}.csv', index_col=0, parse_dates=True)
        return ohlcv

    def run(self, shortable=False):
        # define date range
        bm = self._get_ohlcv(self._benchmark)
        global_start = bm.loc[:self._start].iloc[-self._rollD-1:].index[0]

        # read indicator
        ind = self._get_ohlcv(self._indicator).loc[global_start:self._end]
        
        # iteration
        gaps = pd.Series(name='gaps')
        ufgaps = pd.Series(name='ufgaps')
        for date in ind.index[self._rollD+1:]:
            win = ind.loc[:date].iloc[-self._rollD-1:]
            today, ystd = win.iloc[1], win.iloc[0]
            long, short = +1, -1 if shortable else 0
            if today.Low/ystd.High > 1+self._minWidth/100:
                # if today.name.year==2016: 
                #     print(today.name.date(), ystd.High, win.iloc[1:].Low.min(), ystd.High<win.iloc[1:].Low.min())
                #     br()
                gaps.loc[date] = long
                if win.iloc[1:].Low.min()>ystd.High:
                    ufgaps.loc[date] = long
            elif today.High/ystd.Low < 1-self._minWidth/100:
                # if date.year==2019 and date.month==10: 
                #     print(today.name.date(), ystd.Low, win.iloc[1:].High.max(), ystd.Low>win.iloc[1:].High.max())
                #     br()
                gaps.loc[date] = short                
                if win.iloc[1:].High.max()<ystd.Low:
                    ufgaps.loc[date] = short
            else: 
                gaps.loc[date] = 0
        # ufgaps.plot()
        # plt.show()

        # make signal
        signal = ufgaps.reindex(gaps.index).ffill()
        target_lv = signal*1.0
        
        # calculate portfolio and benchmark nav series
        stk_sr = self._get_ohlcv(self._stock)['Adj Close'].loc[self._start:]
        stk_chg_sr = stk_sr.pct_change()
        porf_chg_sr = stk_chg_sr*target_lv
        porf_nav_sr = pd.Series((1+porf_chg_sr.fillna(0)).cumprod()*self._ininav, name='portfolio')
        porf_bm_sr = pd.Series((1+stk_chg_sr.fillna(0)).cumprod()*self._ininav, name='benchmark')
        account = pd.concat([porf_nav_sr, porf_bm_sr], axis=1)
        
        self._account = account
        self._target_lv = target_lv
        return self

    def evaluate(self, *, show=False):
        def account_metrics(ts):
            chgs = np.log(ts).diff()
            mu = chgs.mean()*252
            sigma = chgs.std()*np.sqrt(252)
            def cal_sharpe(mu, sigma, rf=0.025):
                return (mu - rf)/(sigma)
            sharpe = cal_sharpe(mu, sigma)
            def cal_drawdown(ts):
                run_max = np.maximum.accumulate(ts)
                end = (run_max - ts).idxmax()
                start = (ts.loc[:end]).idxmax()
                low = ts.at[end]
                high = ts.at[start]
                dd = low/high-1
                return dd
            mdd = cal_drawdown(ts)
            def cal_cagr(ts, basis=252):
                cagr = (ts[-1]/ts[0])**(basis/len(ts))-1
                return cagr
            cagr = cal_cagr(ts)
            metrics = {'mu':mu, 'sigma':sigma, 'sharpe':sharpe, 'mdd':mdd, 'cagr':cagr, }
            return metrics
        metrics = {name:account_metrics(ts) for name,ts in self._account.items()}        
        def plot():
            fig, ax = plt.subplots(2,1, figsize=(15,9), sharex=True, constrained_layout=True,
                            gridspec_kw={'width_ratios':[1], 'height_ratios':[3,1]})            
            start, end = self._account.index[0].date(), self._account.index[-1].date()
            return_st = self._account['portfolio'][-1]/self._account['portfolio'][0]-1
            return_bm = self._account['benchmark'][-1]/self._account['benchmark'][0]-1
            metrics_st = ", ".join([f"{k}:{v:.2%}" for k,v in metrics["portfolio"].items()])
            metrics_bm = ", ".join([f"{k}:{v:.2%}" for k,v in metrics["benchmark"].items()])
            maintitle = (f'Performance, start: {start}, end:{end}\n'
                        f'Strategy : {return_st:.2%} ({metrics_st})\n'
                        f'Benchmark: {return_bm:.2%} ({metrics_bm})\n')
            ax[0].set_title(maintitle)
            ax[0].plot(self._account['portfolio'], label='startegy')
            ax[0].plot(self._account['benchmark'], label=f'benchmark({self._benchmark})')
            ax[0].legend()
            subtitle = (f'Target leverage\nSignal: {self._indicator} unfilled gaps, '
                        f'rollD:{self._rollD}, minWidth:{self._minWidth}')
            ax[1].set_title(subtitle)
            ax[1].plot(self._target_lv)
            plt.show(block=True)            
        if show: plot()
        
        return {
            'config':self._config,
            'metrics':metrics
        }

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--start', type=str, default='20000101', help='Start date of backtest')
    parser.add_argument('-e', '--end', type=str, default=None, help='End date of backtest')
    parser.add_argument('-stk', '--stock', type=str, default='^HSI', help='Stock to trade')
    parser.add_argument('-bm', '--benchmark', type=str, default='^HSI', help='Stock as benchmark')
    parser.add_argument('-ind', '--indicator', type=str, default='^HSI', help='Indicator to decide leverage')
    parser.add_argument('-rD', '--rollD', type=int, default=38, help='Rolling window in days to look back')
    parser.add_argument('-mW', '--minWidth', type=float, default=.6, help='Min gap width threadhold in percent')
    parser.add_argument('--ininav', type=int, default=1e7, help='Initial nav')
    sargs = parser.parse_args()

    backtest = Strategy(**vars(sargs))
    backtest.run()
    backtest.evaluate(
        show=True)
if __name__ == "__main__":
    main()