from unittest import expectedFailure
import pytest

from brownie import *
from packages.chainedmetrics import setup, calculate_token_returned
import logging


def test_amm_fund_10_at_50():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})

    assert amm.balanceOf(a.address) == 10**18, "Account should have a balance of 10"
    assert long.balanceOf(amm.address) == 10**18, "AMM should have 10  long tokens"
    assert short.balanceOf(amm.address) == 10**18, "AMM should have 10 short tokens"

def test_amm_fund_13_at_50():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 13*10**18, {'from': a})
    amm.fund(13*10**18, 5*10**7, {'from': a})

    assert amm.balanceOf(a.address) == 13*10**18, "Account should have a balance of 10"
    assert long.balanceOf(amm.address) == 13*10**18, "AMM should have 10  long tokens"
    assert short.balanceOf(amm.address) == 13*10**18, "AMM should have 10 short tokens"

def test_amm_fund_strange_numbers():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 13*10**18, {'from': a})
    amm.fund(13*10**18, 7777777, {'from': a})
    
    assert amm.balanceOf(a.address) == 13*10**18, "Account should have a balance of 10"
    assert long.balanceOf(amm.address) + long.balanceOf(a.address) == short.balanceOf(amm.address) + short.balanceOf(a.address)

def test_amm_fund_twice():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 20*10**18, {'from': a})
    amm.fund(10*10**18, 5*10**7, {'from': a})
    amm.fund(10*10**18, 0, {'from': a})

    assert amm.balanceOf(a.address) == 20*10**18, "Account should have a balance of 10"
    assert long.balanceOf(amm.address) == 20*10**18, "AMM should have 10  long tokens"
    assert short.balanceOf(amm.address) == 20*10**18, "AMM should have 10 short tokens"
    assert short.balanceOf(a.address) == 0, "Account should have no tokens"
    assert long.balanceOf(a.address) == 0, "Account should have no tokens"


def test_target_price_cant_be_reset():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 20*10**18, {'from': a})
    amm.fund(10*10**18, 5*10**7, {'from': a})
    with pytest.raises(Exception) as exc_info:   
        amm.fund(10*10**18, 7*10**7, {'from': a})


def test_target_price_cant_be_above_ten_to_eighth():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 20*10**18, {'from': a})
    with pytest.raises(Exception) as exc_info:   
        amm.fund(10*10**18, 7*10**8, {'from': a})

def test_buy_amm():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})

def test_70_target():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 100*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    
    funding_amount = short.balanceOf(amm) + int(10**19*.98)

    amm.buy(10**19, True, 1)

    expectedAmmount = calculate_token_returned(amm.k(), funding_amount)
    balancingAmount = short.balanceOf(a.address) + int(10**19*.98)

    print(f'k: {amm.k(): >30}')
    print(f'fundingAmount: {funding_amount: >30}')
    print(f'targetBalance: {expectedAmmount: >30}')
    print(f'balancing amount: {balancingAmount: >30}')

    assert long.balanceOf(amm.address) == expectedAmmount

def test_funding_token_is_collateralized():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 100*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    
    assert short.balanceOf(amm.address) == 10**19
    funding_amount = short.balanceOf(amm) + int(10**19*.98)

    amm.buy(10**19, True, 1)

    assert short.balanceOf(amm.address) == funding_amount

    

# def test_amm():
#     a = accounts.add()
#     usdc = ScalarToken.deploy('USDC', 'USDC', {'from': a})
#     usdc.issueTokens(a.address, 100*10**18, {'from': a.address})

#     amm = FixedProductMarketMaker.deploy(
#         'NFLX Subs LP Pool', 'NFLX/SUBS/LP', usdc.address, 'NFLX Subs', 'NFLX/SUBS', {'from': a.address}
#     )

#     usdc.approve(amm.address, 10*10**18, {'from': a})
#     amm.fund(10**18, 5*10**17, {'from': a})

#     amm.buy(10**18, True, 0, {'from': a})

#     longToken = Contract.from_abi('LongToken', amm.longTokenAddress(), ScalarToken.abi)
#     longToken.approve(amm.address, amm.longBalanceOf(a), {'from': a})
#     print(f"USDC Before: {usdc.balanceOf(a)}")
#     print(f"Long Before: {amm.longBalanceOf(a)}")
#     amm.sell(amm.longBalanceOf(a), True, 0)

#     assert longToken.balanceOf(a) == 0, "All Tokens should be sold"
#     print(f"USDC After: {usdc.balanceOf(a)}")