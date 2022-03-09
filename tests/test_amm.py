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
    
def test_setting_outcome_from_other_address():
    a, amm, usdc, long, short = setup()

    a1 = accounts.add()

    with pytest.raises(Exception) as exc_info:   
        amm.set_outcome(75, {'from': a1})

def test_high_equal_low_raises_error():

    with pytest.raises(Exception) as exc_info:   
        setup(high=100, low=100)

def test_high_less_than_low_raises_error():

    with pytest.raises(Exception) as exc_info:   
        setup(high=100, low=101)

def test_get_payout_before_outcome_set():

    a, amm, usdc, long, short = setup()

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})

    with pytest.raises(Exception) as exc_info:   
        amm.get_payout()

def test_get_payout_after_outcome_set():

    a, amm, usdc, long, short = setup(high=100, low=0)

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})
    amm.buy(10**18, True, 1)

    amm.set_outcome(50, {'from': a})

    starting_balance = usdc.balanceOf(a.address)
    starting_long_balance = long.balanceOf(a.address)
    starting_short_balance = short.balanceOf(a.address)
    assert starting_short_balance == 0

    amm.execute_payout()

    assert long.balanceOf(a.address) == 0
    assert short.balanceOf(a.address) == 0

    print(starting_long_balance)
    print(starting_balance)
    assert usdc.balanceOf(a.address) == int(Decimal(starting_long_balance) / 2) + starting_balance

def test_get_payout_after_outcome_set_above_high():

    a, amm, usdc, long, short = setup(high=100, low=0)

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})
    amm.buy(10**18, True, 1)

    amm.set_outcome(200, {'from': a})

    starting_balance = usdc.balanceOf(a.address)
    starting_long_balance = long.balanceOf(a.address)
    starting_short_balance = short.balanceOf(a.address)
    assert starting_short_balance == 0

    amm.execute_payout()

    assert long.balanceOf(a.address) == 0
    assert short.balanceOf(a.address) == 0

    print(starting_long_balance)
    print(starting_balance)
    assert usdc.balanceOf(a.address) == int(Decimal(starting_long_balance)) * 1 + starting_balance

def test_get_payout_after_outcome_set_below_low():

    a, amm, usdc, long, short = setup(high=100, low=3)

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})
    amm.buy(10**18, True, 1)

    amm.set_outcome(2, {'from': a})

    starting_balance = usdc.balanceOf(a.address)
    starting_long_balance = long.balanceOf(a.address)
    starting_short_balance = short.balanceOf(a.address)
    assert starting_short_balance == 0

    amm.execute_payout()

    assert long.balanceOf(a.address) == 0
    assert short.balanceOf(a.address) == 0

    print(starting_long_balance)
    print(starting_balance)
    assert usdc.balanceOf(a.address) == int(Decimal(starting_long_balance)) * 0 + starting_balance

def test_get_payout_after_outcome_set_33():

    a, amm, usdc, long, short = setup(high=100, low=0)

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})
    amm.buy(10**18, True, 1)

    amm.set_outcome(33, {'from': a})

    starting_balance = usdc.balanceOf(a.address)
    starting_long_balance = long.balanceOf(a.address)
    starting_short_balance = short.balanceOf(a.address)
    assert starting_short_balance == 0

    print(starting_long_balance)
    print(starting_balance)
    print(f"Expected: {int(Decimal(starting_long_balance) * Decimal(33/100)) + starting_balance}")
    amm.execute_payout()

    assert long.balanceOf(a.address) == 0
    assert short.balanceOf(a.address) == 0

    assert int(usdc.balanceOf(a.address) / 1000) == int(int(starting_long_balance * Decimal(33/100)) + starting_balance) / 1000

def test_get_payout_after_outcome_short():

    a, amm, usdc, long, short = setup(high=100, low=0)

    usdc.approve(amm.address, 10*10**18, {'from': a})
    amm.fund(10**18, 5*10**7, {'from': a})
    amm.buy(11**18, False, 1)

    amm.set_outcome(50, {'from': a})

    starting_balance = usdc.balanceOf(a.address)
    starting_long_balance = long.balanceOf(a.address)
    starting_short_balance = short.balanceOf(a.address)
    assert starting_long_balance == 0

    amm.execute_payout()

    assert long.balanceOf(a.address) == 0
    assert short.balanceOf(a.address) == 0

    print(starting_long_balance)
    print(starting_balance)
    assert usdc.balanceOf(a.address) == int(Decimal(starting_short_balance)) * Decimal(50/100) + starting_balance