import time
import pyupbit
import pandas
import math
import datetime
import numpy as np
import logging
import telegram                                     #텔레그램 모듈을 가져옵니다.

my_token = '1721040065:AAEL2MdXAUBVCjVQGBWCT2l2tb1sUYcrOVw'   #토큰을 설정해 줍니다.
bot = telegram.Bot(token = my_token)                          #봇을 생성합니다.
chat_id = '@fteamcoin'

formater = logging.Formatter('[%(asctime)s] %(levelname)s:%(message)s')

file_handler = logging.FileHandler("turtle.log")
# stream_handler = logging.StreamHandler()

file_handler.setFormatter(formater)
# stream_handler.setFormatter(formater)

logger = logging.getLogger("logger")
logger.addHandler(file_handler)
# logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

with open("upbit.txt") as f:
    lines = f.readlines()
    access = lines[0].strip()
    secret = lines[1].strip()
    upbit = pyupbit.Upbit(access, secret)
    f.close()

# tickers = ["KRW-BTC", "KRW-ETH", "KRW-SOL"]
tickers = ["KRW-BTC", "KRW-ETH"]
# tickers = ["KRW-BTC"]


def get_df(df, n):
    tempObj = {
        'open': [],
        'high': [],
        'low': [],
        'close': [],
        'volume': [],
        'value': []
    }
    dfLen = math.floor(len(df)/n)
    for i in range(dfLen):
        fromVal = -1*n*i if -1*n*i != 0 else None
        tempObj['open'].append(df.iloc[-1*n*(i+1)]['open'])
        tempObj['high'].append(df.iloc[-1*n*(i+1):fromVal]['high'].max())
        tempObj['low'].append(df.iloc[-1*n*(i+1):fromVal]['low'].min())
        tempObj['close'].append(df.iloc[-1*n*i-1]['close'])
        tempObj['volume'].append(df.iloc[-1*n*(i+1):fromVal]['volume'].sum())
        tempObj['value'].append(df.iloc[-1*n*(i+1):fromVal]['value'].sum())
    resDf = pandas.DataFrame(tempObj)[::-1]
    return resDf


# def cal_atr(symbol):

#     df = pyupbit.get_ohlcv(ticker=symbol, interval="day", count=60)
#     df.tail()

#     df['pclose'] = df['close'].shift(1)
#     df['diff1'] = abs(df['high'] - df['low'])
#     df['diff2'] = abs(df['pclose'] - df['high'])
#     df['diff3'] = abs(df['pclose'] - df['low'])
#     df['TR'] = df[['diff1', 'diff2', 'diff3']].max(axis=1)

#     data = np.array(df['TR'])    # no previous day's N 

#     for i in range(1, len(df)):
#         data[i] = (19 * data[i-1] + df['TR'].iloc[i]) / 20 

#     df['N'] = data

#     atr[symbol] = df['N'][-1]
#     high20[symbol] = df['high'][-21:-1].max()
#     high55[symbol] = df['high'][-56:-1].max()
#     low10[symbol] = df['low'][-11:-1].min()

#     time.sleep(0.1)


def cal_atr(symbol):
    now = datetime.datetime.now()
    df = pyupbit.get_ohlcv(ticker=symbol, interval="minute60", count=733)
    if 9 <= now.hour < 21:
        df = df.iloc[:-(now.hour-8)]
    if 21 <= now.hour <= 24:
        df = df.iloc[:-(now.hour-20)]
    if 0 <= now.hour < 9:
        df = df.iloc[:-(now.hour+4)]

    df = get_df(df, 12)
    df = df.reset_index()

    df.tail()

    df['pclose'] = df['close'].shift(1)
    df['diff1'] = abs(df['high'] - df['low'])
    df['diff2'] = abs(df['pclose'] - df['high'])
    df['diff3'] = abs(df['pclose'] - df['low'])
    df['TR'] = df[['diff1', 'diff2', 'diff3']].max(axis=1)

    data = np.array(df['TR'])    # no previous day's N 

    for i in range(1, len(df)):
        data[i] = (19 * data[i-1] + df['TR'].iloc[i]) / 20 


    df['N'] = data

    atr[symbol] = round(df['N'][-1:].max())
    high20[symbol] = round(df['high'][-20:].max(), 3)
    high55[symbol] = round(df['high'][-55:].max(), 3)
    low10[symbol] = round(df['low'][-10:].min(), 3)
    low20[symbol] = round(df['low'][-20:].min(), 3)


def cal_unit(symbol, krw):
    unit[symbol] = round((((krw * 0.02) / len(tickers))/2)/atr[symbol], 3)


def buy_coin1():
    global coin_num
    for symbol in tickers:
        coin_price = pyupbit.get_current_price(symbol)
        if coin_price >= high20[symbol] and coin_price < high55[symbol] and holdings[symbol] is False:
            amount = coin_price * float(unit[symbol])
            upbit.buy_market_order(symbol, amount)
            text = '시스템1 매수: {}, 가격: {:,}원'.format(symbol, coin_price)
            bot.sendMessage(chat_id=chat_id, text=text)
            logger.info(text)
            holdings[symbol] = True
            buy_price[symbol] = coin_price
            buy_num[symbol] = 1
            coin_num = coin_num - 1
        time.sleep(0.1)


def buy_coin2(krw):
    for symbol in tickers:
        coin_price = pyupbit.get_current_price(symbol)
        amount = coin_price * float(unit[symbol])
        if holdings[symbol] is True and coin_price >= (buy_price[symbol] + (atr[symbol]/2)) and buy_num[symbol] < 5:         # 현재가 > 15ma
            buy_price[symbol] = coin_price
            buy_num[symbol] = buy_num[symbol] + 1
            if krw > amount:
                upbit.buy_market_order(symbol, amount)
                text = '시스템1 매수: {}, 가격: {:,}원'.format(symbol, coin_price)
                bot.sendMessage(chat_id=chat_id, text=text)
                logger.info(text)
        time.sleep(0.1)


def buy_coin3(krw):
    for symbol in tickers:
        coin_price = pyupbit.get_current_price(symbol)
        amount = coin_price * float(unit[symbol])
        if coin_price >= high55[symbol] and holdings2[symbol] is False:
            buy_price[symbol] = coin_price
            buy_num[symbol] = 6
            holdings[symbol] = True
            holdings2[symbol] = True
            if krw > amount:
                upbit.buy_market_order(symbol, amount)
                text = '시스템2 매수: {}, 가격: {:,}원'.format(symbol, coin_price)
                bot.sendMessage(chat_id=chat_id, text=text)
                logger.info(text)
        time.sleep(0.1)


def buy_coin4(krw):
    for symbol in tickers:
        coin_price = pyupbit.get_current_price(symbol)
        amount = coin_price * float(unit[symbol])
        if holdings2[symbol] is True and coin_price >= (buy_price[symbol] + (atr[symbol]/2)) and 6 <= buy_num[symbol] < 10:         # 현재가 > 15ma
            buy_price[symbol] = coin_price
            buy_num[symbol] = buy_num[symbol] + 1
            if krw > amount:
                upbit.buy_market_order(symbol, amount)
                text = '시스템2 매수: {}, 가격: {:,}원'.format(symbol, coin_price)
                bot.sendMessage(chat_id=chat_id, text=text)
                logger.info(text)
        time.sleep(0.1)


def sell_coin():
    global coin_num
    for symbol in tickers:
        coin_price = pyupbit.get_current_price(symbol)
        if (holdings[symbol] is True) and (holdings2[symbol] is False) and \
            ((coin_price < (buy_price[symbol] - (atr[symbol]*2))) or \
            coin_price < low10[symbol]):
            coin_balance = upbit.get_balance(symbol)
            upbit.sell_market_order(symbol, coin_balance)
            text = '매도: {}, 매도가: {:,}원'.format(symbol, coin_price)
            bot.sendMessage(chat_id=chat_id, text=text)
            holdings[symbol] = False
            holdings2[symbol] = False

            coin_num = coin_num + 1

            krw = get_krw()

            cal_atr(symbol)
            cal_unit(symbol, krw)

        elif holdings2[symbol] is True and \
            ((coin_price < (buy_price[symbol] - (atr[symbol]*2))) or \
            coin_price < low20[symbol]):
            coin_balance = upbit.get_balance(symbol)
            upbit.sell_market_order(symbol, coin_balance)
            text = '매도: {}, 매도가: {:,}원'.format(symbol, coin_price)
            bot.sendMessage(chat_id=chat_id, text=text)
            holdings[symbol] = False
            holdings2[symbol] = False

            coin_num = coin_num + 1

            krw = get_krw()

            cal_atr(symbol)
            cal_unit(symbol, krw)

        time.sleep(0.1)

def get_krw():
    krw_balance = upbit.get_balance(ticker="KRW")
    # coin_balance = 0
    coin_balance = upbit.get_amount('ALL')
    # for ticker in tickers:
    #    a = pyupbit.get_current_price(ticker) * upbit.get_balance(ticker)
    #     coin_balance = coin_balance + a
    #     time.sleep(0.1)
    krw = krw_balance + coin_balance
    return krw

def get_krw9():
    krw_balance = upbit.get_balance(ticker="KRW")
    coin_balance = 0
    # coin_balance = upbit.get_amount('ALL')
    for ticker in tickers:
        a = pyupbit.get_current_price(ticker) * upbit.get_balance(ticker)
        coin_balance = coin_balance + a
        time.sleep(0.1)
    krw = krw_balance + coin_balance
    return krw


def money_status(krw):                    # 잔고현황을 텔레그램 봇으로 전송
    with open("money.txt") as f:
        lines = f.readlines()
        money = float(lines[0].strip())
        f.close()

    profits = krw - money
    profits_rate = ((krw / money)-1) * 100
    text = '코인거래 진행상황\n\n평가액: {:,}원,\n수익금: {:,}원,\n수익율: {:>0.1f}%\n\n오늘도 화이팅'.format(int(krw), int(profits), profits_rate)
    bot.sendMessage(chat_id=chat_id, text=text)
    time.sleep(0.1)

def status():                    # 현상황 로그기록
    for symbol in tickers:
        cal_atr(symbol)
        cal_unit(symbol, krw)

        text0 = symbol
        text1 = "atr : {:,}".format(atr[symbol])
        text2 = "unit : {:,}".format(unit[symbol])
        text3 = "high20 : {:,}".format(high20[symbol])
        text4 = "high55 : {:,}".format(high55[symbol])
        text5 = "low10 : {:,}".format(low10[symbol])
        text6 = "low20 : {:,}".format(low20[symbol])
        text7 = "holdings : " + str(holdings[symbol])
        text8 = "holdings2 : " + str(holdings2[symbol]) + "\n"
        logger.info(text0)
        logger.info(text1)
        logger.info(text2)
        logger.info(text3)
        logger.info(text4)
        logger.info(text5)
        logger.info(text6)
        logger.info(text7)

        if holdings[symbol] is True and holdings2[symbol] is False:
            loss_price = int(buy_price[symbol]-(atr[symbol] * 2))
            text8 = "holdings2 : " + str(holdings2[symbol])
            text9 = "buy_price : {:,}".format(buy_price[symbol])
            text10 = "loss price1 : {:,}".format(loss_price)
            text11 = "loss price2 : {:,}".format(low10[symbol])
            logger.info(text8)
            logger.info(text9)
            logger.info(text10)
            logger.info(text11)
            if loss_price > low10[symbol]:
                text13 = "loss price : {:,}".format(loss_price) + "\n"
                logger.info(text13)
                text14 = "{} 손절가 : {:,}".format(symbol, loss_price)
                bot.sendMessage(chat_id=chat_id, text=text14)
            else:
                text13 = "loss price : {:,}".format(low10[symbol]) + "\n"
                logger.info(text13)
                text14 = "{} 손절가 : {:,}".format(symbol, low10[symbol])
                bot.sendMessage(chat_id=chat_id, text=text14)

        elif holdings2[symbol] is True:
            loss_price = int(buy_price[symbol]-(atr[symbol] * 2))
            text8 = "holdings2 : " + str(holdings2[symbol])
            text9 = "buy_price : {:,}".format(buy_price[symbol])
            text10 = "loss price1 : {:,}".format(loss_price)
            text11 = "loss price2 : {:,}".format(low20[symbol])
            logger.info(text8)
            logger.info(text9)
            logger.info(text10)
            logger.info(text11)
            if loss_price > low20[symbol]:
                text13 = "loss price : {:,}".format(loss_price) + "\n"
                logger.info(text13)
                text14 = "{} 손절가 : {:,}".format(symbol, loss_price)
                bot.sendMessage(chat_id=chat_id, text=text14)
            else:
                text13 = "loss price : {:,}".format(low20[symbol]) + "\n"
                logger.info(text13)
                text14 = "{} 손절가 : {:,}".format(symbol, low20[symbol])
                bot.sendMessage(chat_id=chat_id, text=text14)
        else:
            logger.info(text8)

#-------------------------------------------------------------------------
# 알고리즘 시작
#-------------------------------------------------------------------------

atr, high20, high55, low10, low20, unit = {}, {}, {}, {}, {}, {}
buy_price, buy_num = {}, {}
holdings = {ticker:False for ticker in tickers}
holdings2 = {ticker:False for ticker in tickers}

krw = get_krw()

# 재실행용 필요데이터

# buy_price['KRW-BTC'] = 53940000.0
# buy_num['KRW-BTC'] = 6
# holdings['KRW-BTC'] = True
# holdings2['KRW-BTC'] = True

# buy_price['KRW-ETH'] = 3877000.0
# buy_num['KRW-ETH'] = 3
# holdings['KRW-ETH'] = True
# holdings2['KRW-ETH'] = True

# krw9 = get_krw9()
# money_status(krw9)
# 재실행용 필요데이터

status()

coin_num = len(tickers)
op_mode = True

while True:
    try:
        now = datetime.datetime.now()
        if (now.hour == 8 or now.hour == 20) and now.minute == 59 and (50 <= now.second < 59) and op_mode is True:
            op_mode = False

        if (now.hour == 9 or now.hour == 21) and now.minute == 0 and (10 <= now.second < 20) and op_mode is False:
            krw9 = get_krw9()
            money_status(krw9)
            
            status()

            op_mode = True
            time.sleep(1)

        krw_now = upbit.get_balance(ticker="KRW")
        buy_coin1()
        buy_coin2(krw_now)
        buy_coin3(krw_now)
        buy_coin4(krw_now)
        sell_coin()
        time.sleep(0.1)

    except Exception as e:
        logger.warning(e)
        #bot.sendMessage(chat_id=chat_id, text="오류확인")
        time.sleep(1)