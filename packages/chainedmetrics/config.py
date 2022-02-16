from brownie import *
from decimal import Decimal

def setup():

    a = accounts.add()
    usdc = ScalarToken.deploy('USDC', 'USDC', {'from': a})
    usdc.issueTokens(a.address, 100*10**18, {'from': a.address})

    amm = FixedProductMarketMaker.deploy(
        'NFLX Subs LP Pool', 'NFLX/SUBS/LP', usdc.address, 'NFLX Subs', 'NFLX/SUBS', {'from': a.address}
    )

    longToken = Contract.from_abi('LongToken', amm.longTokenAddress(), ScalarToken.abi)
    shortToken = Contract.from_abi('ShortToken', amm.shortTokenAddress(), ScalarToken.abi)

    return (a, amm, usdc, longToken, shortToken)

def calculate_token_returned(k, fundingToken):

    return int(Decimal(k) / Decimal(fundingToken))

def calculate_target_funding_amount(target, fundingToken):

    return 10 ** 8 * int(fundingToken / target) - fundingToken

    