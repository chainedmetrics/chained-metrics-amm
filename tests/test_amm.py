import pytest

from brownie import *
from unittest import expectedFailure
from packages.chainedmetrics import setup, calculate_token_returned, calculate_target_funding_amount
from decimal import Decimal


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

    expectedAmmount = calculate_token_returned(amm.K(), funding_amount)
    balancingAmount = short.balanceOf(a.address) + int(10**19*.98)

    print(f'k: {amm.K(): >30}')
    print(f'fundingAmount: {funding_amount: >30}')
    print(f'targetBalance: {expectedAmmount: >30}')
    print(f'balancing amount: {balancingAmount: >30}')

    assert long.balanceOf(amm.address) == expectedAmmount

def test_many_orders():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 100*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    multiple = 3.141592653
    for _ in range(20):
        print(_)
        funding_amount = Decimal(short.balanceOf(amm)) + int(Decimal(multiple * 10 ** 18 / 100)) * 98
        print(f"investmentAmount:          {int(int(Decimal(multiple)*10 ** 18))}")
        print(f"investmentAmountMinusFee:  {int(Decimal(multiple * 10 ** 18) * Decimal(.98))}")
        print(f"k:                         {amm.K()}")
        print(f"fundingToken.balanceOfThis {funding_amount}")
        amm.buy(int(Decimal(multiple * 10 ** 18)), True, 1)

        
        expectedAmmount = calculate_token_returned(Decimal(amm.K()), Decimal(funding_amount))
        assert long.balanceOf(amm.address) == expectedAmmount
        amm.buy(4**18, False, 1)
        amm.buy(2**18, False, 1)

def test_many_large_orders():
    a, amm, usdc, long, short = setup(10000000)

    usdc.approve(amm.address, 100000000*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    multiple = 219082.14159265
    for _ in range(20):
        funding_amount = Decimal(short.balanceOf(amm)) + int(Decimal(multiple * 10 ** 18 / 100)) * 98
        amm.buy(int(Decimal(multiple * 10 ** 18)), True, 1)

        
        expectedAmmount = calculate_token_returned(Decimal(amm.K()), Decimal(funding_amount))
        assert long.balanceOf(amm.address) == expectedAmmount
        amm.buy(4**18, False, 1)
        amm.buy(2**18, False, 1)

def test_funding_token_is_collateralized():
    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 100*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    
    assert short.balanceOf(amm.address) == 10**19
    funding_amount = short.balanceOf(amm) + int(10**19*.98)

    amm.buy(10**19, True, 1)

    assert short.balanceOf(amm.address) == funding_amount


def test_sell_order():
    a, amm, usdc, long, short = setup(10000000)

    usdc.approve(amm.address, 10000000*10**18, {'from': a})
    long.approve(amm.address, 10000000*10**18, {'from': a})
    amm.fund(10**19, 7*10**7, {'from': a})
    
    funding_amount = short.balanceOf(amm) + int(10**19*.98)

    amm.buy(10**19, True, 1)
    amm.sell(long.balanceOf(a.address), True, 1)

    assert long.balanceOf(a.address) == 0
    assert amm.calculateCurrentProbability(long.balanceOf(amm.address), short.balanceOf(amm.address)) == 5*10**7
    print(long.balanceOf(amm.address))
    print(short.balanceOf(amm.address))
    print(amm.calculateCurrentProbability(long.balanceOf(amm.address), short.balanceOf(amm.address)))

def test_many_buys_and_sells():
    a, amm, usdc, long, short = setup(1000000000)
    usdc.approve(amm.address, 100000000*10**18, {'from': a})

    amm.fund(10**20, 7*10**7, {'from': a})
    startingLong = long.balanceOf(amm.address)
    startingShort = short.balanceOf(amm.address)

    order_sizes1 = [i*10**18 for i in range(1, 20)]
    order_sizes2 = [3.17*10**18 for i in range(1, 20)]
    order_sizes3 = [2.5*10**18 for i in range(1, 20)]

    a1 = accounts.add()
    a2 = accounts.add()
    a3 = accounts.add()

    for account in [a1, a2, a3]:
        usdc.transfer(account, 10000000*10**18, {'from': a})
        usdc.approve(amm.address, 10000000*10**18, {'from': account})
        long.approve(amm.address, 10000000*10**18, {'from': account})
        short.approve(amm.address, 10000000*10**18, {'from': account})

    for (o1, o2, o3) in zip(order_sizes1, order_sizes2, order_sizes3):
        amm.buy(o1, True, 1, {'from': a1})
        amm.buy(o2, False, 1, {'from': a2})
        amm.buy(o3, True, 1, {'from': a3})

        amm.sell(2*10**16, True, 1, {'from': a1})
    
    amm.sell(long.balanceOf(a1.address), True, 1, {'from': a1})
    amm.sell(short.balanceOf(a2.address), False, 1, {'from': a2})
    amm.sell(long.balanceOf(a3.address), True, 1, {'from': a3})

    # After a lot of trading confirm the holdings of the amm are the same as the starting balance
    assert short.balanceOf(amm.address) > startingShort
    assert long.balanceOf(amm.address) > startingLong
    assert int(short.balanceOf(amm.address)/100) == int(startingShort / 100)
    assert int(long.balanceOf(amm.address)/100) == int(startingLong / 100)
    
