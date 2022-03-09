from brownie import *
from decimal import Decimal

def setup(usdc_amount=100, usdc_address=None, a=None, high=100, low=50):

    if not a:
        a = accounts.add()

    if not usdc_address:
        usdc = ScalarToken.deploy('USDC', 'USDC', {'from': a})
    else:
        usdc = Contract.from_abi('USDC', usdc_address, ScalarToken.abi)

    usdc.issueTokens(a.address, usdc_amount*10**18, {'from': a.address})

    amm = FixedProductMarketMaker.deploy(
        'NFLX Subs LP Pool', 'NFLX/SUBS/LP', usdc.address, 
        'NFLX Subs', 'NFLX/SUBS', high, low, a.address, {'from': a.address}
    )

    longToken = Contract.from_abi('LongToken', amm.longTokenAddress(), ScalarToken.abi)
    shortToken = Contract.from_abi('ShortToken', amm.shortTokenAddress(), ScalarToken.abi)

    return (a, amm, usdc, longToken, shortToken)

def calculate_token_returned(k, fundingToken):

    return int(Decimal(int(Decimal(k))) / Decimal(fundingToken))

def calculate_target_funding_amount(target, fundingToken):

    return 10 ** 8 * int(fundingToken / target) - fundingToken

    