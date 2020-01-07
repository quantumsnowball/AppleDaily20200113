br = breakpoint
import os, itertools
import pandas as pd
from backtest import Strategy

def main():
    var_fields = {
        'rollD': range(6, 251, 2),
        'minWidth': (i/10 for i in range(20)),
    } 
    combos = [{
        'start': '20000101',
        'end': None,
        'stock': '^HSI',
        'benchmark': '^HSI',
        'indicator': '^HSI',        
        'rollD': rD,
        'minWidth': mW,
        'ininav': 1.0e7,
    } for rD,mW in itertools.product(*tuple(var_fields.values()))]

        
    for i,combo in enumerate(combos):
        try:
            def trial(combo, i, n):        
                result = Strategy(**combo).run().evaluate()
                cur = {n:result['config'][n] for n in var_fields.keys()}
                print(f'{i+1: >5} / {n} | config: {cur}', end=' | ')
                return result
            result = trial(combo, i, len(combos))
            def pack(res):
                data = {}
                for key,val in res['config'].items():
                    data[key] = val
                for key,val in res['metrics']['portfolio'].items():
                    data[key] = val
                for key,val in res['metrics']['benchmark'].items():
                    data[key+'_bm'] = val
                return pd.DataFrame(data, index=[i])
            package = pack(result)
            def save(package, filename='score.csv'):            
                d = {'mode':'a', 'header':False} if os.path.isfile(filename) else {}
                package.to_csv(filename, **d)
            save(package)
            print('Success', end='       \n')
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(str(e))
            continue

    df = pd.read_csv('score.csv', index_col=0).sort_values(by='sharpe', ascending=False).reset_index(drop=True)
    print(df)

if __name__ == "__main__":
    main()