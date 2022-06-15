import time
import os
import urllib.parse
from typing import Optional, Dict, Any, List
from requests import Request, Session, Response
import hmac

#API keys imported via google secrets.
FTX_API_KEY =   'rj5aZiwhfD-sqrtwyYMaWsUfs5CZGhS1oAOnlyQK'#os.getenv('FTX_API_KEY')
FTX_API_SECRET = 'cSsBivWM_d7S7hBE10dJa-yfAEJ6T5c1RTSEuTUC'#os.getenv('FTX_API_SECRET')

class FtxClient:
    """FTX REST API Python client."""
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=FTX_API_KEY, api_secret=FTX_API_SECRET, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def get_future(self, future_name: str = None) -> dict:
        return self._get(f'futures/{future_name}')

    def get_account_info(self) -> dict:
        return self._get(f'account')

    def place_order(self, market: str, side: str, price: float, size: float, type: str = 'limit',
                    reduce_only: bool = False, ioc: bool = False, post_only: bool = False,
                    client_id: str = None, reject_after_ts: float = None) -> dict:
        return self._post('orders', {
            'market': market,
            'side': side,
            'price': price,
            'size': size,
            'type': type,
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only,
            'clientId': client_id,
            'rejectAfterTs': reject_after_ts
        })

    def get_positions(self, show_avg_price: bool = False) -> List[dict]:
        return self._get('positions', {'showAvgPrice': show_avg_price})

    def get_position(self, name: str, show_avg_price: bool = False) -> dict:
        return next(filter(lambda x: x['future'] == name, self.get_positions(show_avg_price)), None)

    def get_single_market(self, market: str = None) -> Dict:
        return self._get(f'markets/{market}')


def hu_auto_trader(request):
    """Accepts TradingView alert webhook post requests and utilises FTX client to place trades automatically."""

    #POST request filter.
    if request.method == 'POST':

        #TradingView alert data extraction.
        signal = request.json
        strategy = signal['strategy']
        market = signal['market']
        ftx_subaccount = signal['ftx_subaccount']
        side = signal['side']
        signal_price = signal['price']
        action = signal['action']

        #If trade action is only closing a position, set Reduce Only to True. 
        if action == "close long" or action == "close short":
            reduce_only = True
        else:
            reduce_only = False
            
        #FtxClient intialisation for FTX subaccount.
        ftx = FtxClient(subaccount_name=ftx_subaccount)

        #Get account info.
        account_info = ftx.get_account_info()
        subaccount_total_usd_value = account_info['totalAccountValue']

        #Get FTX market data.
        market_data = ftx.get_single_market(market)
        ftx_price = market_data['price']
        underlying = market_data['underlying']

        #Get current FTX position.
        position = ftx.get_position(market)

        #If there is no trading history for this subaccount and this market, ftx returns a None type for get_position, so set current position size to 0.0.
        if position == None:
            current_position_size = 0.0
        #Else set current position size to equal current market position size.
        else:
            current_position_size = position['size']
        
        #If Reduce Only is True; set position size equal to current position size.
        if reduce_only == True:
            position_size = current_position_size
        else:
            #Else if no current position; set position size equal to 100% of subaccount equity.
            if current_position_size == 0.0:
                position_size = subaccount_total_usd_value/(ftx_price)
            #Else set position size equal to current position size plus 100% of subaccount equity.
            else:
                position_size = current_position_size + subaccount_total_usd_value/(ftx_price)

        #Print signal and trade info to cloud logs.
        print(f"*New Trade Signal*\nStrategy: {strategy}\nMarket: {market}\nSide: {side}\nAction: {action}\nReduce Only: {reduce_only}\nSignal Price: ${signal_price}\nFTX Price: ${ftx_price}\nSubaccount Total USD Value: ${subaccount_total_usd_value}\nPosition Size: {position_size} {underlying}")
        
        #Only trade if position size is more than zero.
        if position_size > 0.0:
            try:
                #Place order on FTX.
                ftx.place_order(market=market, side=side, price=None, size=position_size, reduce_only=reduce_only, type='market')
                #Log success message in cloud logs.
                print("Trade placed.")
                return "trade placed."

            #Log exceptions.
            except Exception as e:
                print("Trade failed.")
                print(e)
                return ("trade failed")

        #Log when no trades are placed.
        else:
            print("No trade placed.")
            return "No trade placed."

    
jaka = FtxClient()