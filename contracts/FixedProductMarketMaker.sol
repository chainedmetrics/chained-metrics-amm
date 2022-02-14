
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.6;

import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ScalarToken} from "./ScalarToken.sol";
import {SafeMath} from "@openzeppelin/contracts/math/SafeMath.sol";
import {EIP712MetaTransaction} from "./EIP712MetaTransaction.sol";
import {Math} from "./Math.sol";

// For debugging import hardhat for debugging with console.log("Msg");
import "hardhat/console.sol";


contract FixedProductMarketMaker is ERC20, EIP712MetaTransaction('FixedProductMarketMaker', "1") {
    using SafeMath for uint;
    using SafeMath for int;

    ERC20 public collateralToken;
    ScalarToken public longToken;
    ScalarToken public shortToken;

    uint public k;
    uint public constant FEE = 2*10**16;
    mapping (address => uint) public earnedFees;
    address[] public stakers;
    uint constant ONE = 10**18;
    uint constant TARGET_PRICE_DIGITS = 10**8;
    uint constant FIFTY_FIFTY = 5*10**7;
    uint public feePool = 0;

    // Used for quadratic equation and need to be cast to uints
    uint constant UINT_2 = 2;
    uint constant UINT_4 = 4;
    
    event Deposit(string msg); 

    constructor(string memory tokenName, string memory tokenSymbol, address collateralTokenAddress,
        string memory kpiName, string memory kpiSymbol) ERC20(tokenName,  tokenSymbol) public {

        collateralToken = this;
        string memory longName = string(abi.encodePacked(kpiName, " LONG"));
        string memory longSymbol = string(abi.encodePacked(kpiName, "/L"));
        string memory shortName = string(abi.encodePacked(kpiName, " SHORT"));
        string memory shortSymbol = string(abi.encodePacked(kpiName, "/S"));

        longToken = new ScalarToken(longName, longSymbol);
        shortToken = new ScalarToken(shortName, shortSymbol);

        collateralToken = ERC20(collateralTokenAddress);

    }

    function fund(uint fundingAmount, uint targetLongPrice) public{
        /*
        Provides funding for a market and sets the targetLongPrice.

        Arguments:
            fundingAmount: Amount of funding to be provided.
            targetLongPrice: The target price for the long position based on the AMM
        */
        uint longBalance = longToken.balanceOf(address(this));
        uint shortBalance = shortToken.balanceOf(address(this));

        require(fundingAmount >= ONE, 'Minimum funding amount of 1 collateralToken is required');
        if (targetLongPrice > 0){
            require(longBalance == 0 && longBalance == 0, 'Target price can only be set when funding a new market');
            require(targetLongPrice < TARGET_PRICE_DIGITS, 'Target price must be less than 1**8');
        }
        else{
            require (longBalance > 0 && shortBalance > 0, 'Target price must be set before funding a new market');
            targetLongPrice = calculateCurrentProbability(longBalance, shortBalance);
            attributeFees();
        }

        collateralToken.transferFrom(msgSender(), address(this), fundingAmount);

        ScalarToken fundingToken;
        ScalarToken balancingToken;
        if (targetLongPrice >= FIFTY_FIFTY){
            fundingToken = shortToken;
            balancingToken = longToken;
        }
        else{
            fundingToken = longToken;
            balancingToken = shortToken;
            targetLongPrice = TARGET_PRICE_DIGITS.sub(targetLongPrice);
        }

        uint balancingAmount = calculateBalancingQuantity(fundingAmount, targetLongPrice);
        uint returnBalancingAmount = fundingAmount.sub(balancingAmount);
        
        fundingToken.issueTokens(address(this), fundingAmount);
        balancingToken.issueTokens(address(this), balancingAmount);
        balancingToken.issueTokens(msgSender(), returnBalancingAmount);

        console.log("targetLongPrice:      %s", targetLongPrice);
        console.log("fundingAmount         %s", fundingAmount);
        console.log("balancingAmt           %s", balancingAmount);
        console.log("returnBalancingAmount %s", returnBalancingAmount);
        console.log("sender Balance         %s", balancingToken.balanceOf(msgSender()));
        console.log("amm Balance            %s", balancingToken.balanceOf(address(this)));

        k = balancingToken.balanceOf(address(this)).mul(fundingToken.balanceOf(address(this)));

        _mint(msgSender(), fundingAmount);
    
    }

    function longBalanceOf(address _address) public view returns(uint balance){
        return longToken.balanceOf(_address);
    }

    function shortBalanceOf(address _address) public view returns(uint balance){
        return shortToken.balanceOf(_address);
    }

    function longTokenAddress() public view returns (address){
        return address(longToken);
    }

    function shortTokenAddress() public view returns (address){
        return address(shortToken);
    }

    function buy (uint investmentAmount, bool long, uint minOutcomeTokensToBuy) external {

        uint feeAmount = investmentAmount.mul(FEE).div(ONE);
        uint investmentAmountMinusFees = investmentAmount.sub(feeAmount); 
        ScalarToken fundingToken;
        ScalarToken balancingToken;
        if (long) {
            fundingToken = shortToken;
            balancingToken = longToken;
        }
        else {
            fundingToken = longToken;
            balancingToken = shortToken;
        }

        // fully collateralize the tokens
        collateralToken.transferFrom(msgSender(), address(this), investmentAmount);
        fundingToken.issueTokens(address(this), investmentAmountMinusFees);
        balancingToken.issueTokens(address(this), investmentAmountMinusFees);
        feePool = feePool.add(feeAmount);

        uint targetBalancingQuantity = k.div(fundingToken.balanceOf(address(this)));
        uint balancingQuantityReturned = balancingToken.balanceOf(address(this)).sub(targetBalancingQuantity);

        balancingToken.transfer(msgSender(), balancingQuantityReturned);
    }

    function sell (uint sellAmount, bool long, uint minimumReturnAmount) external{
       
        if (long){
            longToken.transferFrom(msgSender(), address(this), sellAmount);
        }
        else{
            shortToken.transferFrom(msgSender(), address(this), sellAmount);
        }

        uint startingLongBalance = longToken.balanceOf(address(this));
        uint startingShortBalance = shortToken.balanceOf(address(this));

        uint a = 1;
        uint b = startingLongBalance.add(startingShortBalance);
        uint c = startingLongBalance.mul(startingShortBalance).sub(k);

        uint burnAmount = solveQuadraticEquation(a, b, c);

        require(startingLongBalance > burnAmount, 'Cannot burn more LONG tokens than existing balance');
        require(startingShortBalance > burnAmount, 'Cannot burn more SHORT tokens than existing balance');
        require(startingLongBalance.sub(burnAmount).mul(startingShortBalance.sub(burnAmount)) == k, 'Invariant formula failed');
        
        longToken.burnTokens(address(this), burnAmount);
        shortToken.burnTokens(address(this), burnAmount);

        uint fee = burnAmount.mul(FEE).div(ONE);
        feePool.add(fee);
        uint returnAmount = burnAmount.sub(fee);

        require(returnAmount >= minimumReturnAmount, 'Minimum return amount not met');
        collateralToken.transfer(msgSender(), returnAmount);
    }

    function calculateCurrentProbability(uint longBalance, uint shortBalance) view public returns(uint currentProbability){
        // Calculated to 8 decimal places of accuracy using 18 decimal token
        currentProbability = shortBalance.div(shortBalance.add(longBalance).div(10**8));
    }

    function calculateBalancingQuantity(uint fundingAmount, uint targetProbability) view public returns(uint balancingQuantity){
        // P(L) = S / (S + L) || P(S) = L / (S + L)
        // ie. L = [S / P(L)] - S
        // Below example funding amount is always equal to token NOT bought

        balancingQuantity = TARGET_PRICE_DIGITS.mul(fundingAmount.div(targetProbability)).sub(fundingAmount);
    }

    function attributeFees() internal{
        // Sets the earned fee allocation to the current LPers
        bool senderSeen = false;
        if (feePool > 0){
            for (uint i = 0; i < stakers.length; i++){
                if (stakers[i] == msgSender()){
                    senderSeen = true;
                }
                earnedFees[stakers[i]] = earnedFees[stakers[i]].add(feePool.mul(balanceOf(stakers[i])).div(totalSupply()));
            }
        }
        if (!senderSeen){
            stakers.push(msgSender());
            earnedFees[msgSender()] = 0;
        }
    }
    
    function solveQuadraticEquation(uint a, uint b, uint c) public view returns(uint x){
        // Solving the formula: ax**2 + bx + c = 0
        // Using the quadradic formula: x = [- b + sqrt(b**2 – 4ac)]/2a 
        // k = (Long - x) * (Short - x)
        // Leads to: k = (Long * Short) - (Long + Short) * X + X**2
        // a = 1; b = -1 * (Long + Short); c = (Long * Short) - k
        // Unmodified example below
        // x = (-1).mul(b).sub(Math.sqrt(b.mul(b).sub(4.mul(a).mul(c)))).div(2.mul(a));

        // There is 1 modificaiton where we remove the negatives and only deal with uints
        // This is achievable because b**2 - 4ac is always positive
        // Results in B = (Long + Short) and x = [b + sqrt(b**2 – 4ac)]/2a

        require(b.mul(b) > UINT_4.mul(a).mul(c), 'Cannot solve quadratic equation');

        x = b.sub(Math.sqrt(b.mul(b).sub(UINT_4.mul(a).mul(c)))).div(UINT_2.mul(a));

        require(x > 0, 'Result is not positive');
    
    }
}