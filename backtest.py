from backtesting.lw_breakout_btest import LWBreakout

# Set start fresh to True if you want to download new data
lw_breakout = LWBreakout(300, start_fresh=False)
lw_breakout.download_data()
lw_breakout.populate_results()
