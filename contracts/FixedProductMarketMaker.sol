
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.6;
pragma experimental ABIEncoderV2;

import {ERC20Upgradeable} from "@openzeppelin-upgradable/contracts/token/ERC20/ERC20Upgradeable.sol";
import {IERC20} from "@openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {Initializable} from "@openzeppelin-upgradable/contracts/proxy/Initializable.sol";
import {AccessControlUpgradeable} from "@openzeppelin-upgradable/contracts/access/AccessControlUpgradeable.sol";
import {SafeMathUpgradeable} from "@openzeppelin-upgradable/contracts/math/SafeMathUpgradeable.sol";
import {EIP712MetaTransaction} from "./EIP712MetaTransaction.sol";
import {ScalarToken} from "./ScalarToken.sol";
import {Math} from "./Math.sol";

// For debugging import hardhat for debugging with console.log("Msg");
// import "hardhat/console.sol";

// Struct with all infor needed to create a new KPI market
struct KPIReferenceData {
    address longAddress;
    address shortAddress;
    address collateralAddress;
    address reportingAddress;
    uint high;
    uint low;
    uint fee;
}

contract FixedProductMarketMaker is Initializable, ERC20Upgradeable, AccessControlUpgradeable, EIP712MetaTransaction('FPAMM', "1")  {
    using SafeMathUpgradeable for uint;

    // REPORTING_ROLE allows an address to report on the outcome of a market
    bytes32 public constant REPORTING_ROLE = keccak256("REPORTING_ROLE");
    
    // Tokens used for collateral and long/short pair for the market
    IERC20 public collateralToken;
    ScalarToken public longToken;
    ScalarToken public shortToken;

    uint public FEE;
    mapping (address => uint) public earnedFees;
    address[] public stakers;

    uint public feePool;

    // Variables used for managing the payout
    uint public high;
    uint public low;
    uint public outcome;
    bool public outcomeSet;

    // Constants used in various calculations
    uint constant ONE = 10**18;
    uint constant TARGET_PRICE_DIGITS = 10**8; // Payouts and initial AMM price go to 8 digits
    uint constant FIFTY_FIFTY = 5*10**7; // 50/50 if using 8 digits of precision
    uint constant UINT_2 = 2;
    uint constant UINT_4 = 4;
    
    event Deposit(string msg); 

    constructor () public{}

    function initialize(KPIReferenceData memory kpiData) public {

        longToken = ScalarToken(kpiData.longAddress);
        shortToken = ScalarToken(kpiData.shortAddress);
        collateralToken = IERC20(kpiData.collateralAddress);


        require(kpiData.high > kpiData.low, "high must be greater than low");
        high = kpiData.high;
        low = kpiData.low;

        FEE = kpiData.fee;

        _setupRole(REPORTING_ROLE, kpiData.reportingAddress);
    }

    function set_outcome(uint _outcome) public {
        // Called by the creator to set the outcome of the market
        require(hasRole(REPORTING_ROLE, msgSender()), "Address does not have REPORTING_ROLE");
        
        if (_outcome <= low){
            outcome = low;
        } else if (_outcome >= high){
            outcome = high;
        } else {
            outcome = _outcome;
        }

        outcomeSet = true;
    }

    function execute_payout() public {
        // Called by the holder of a token to execute their payout
        require(outcomeSet,  "Outcome has not been set");

        uint longBalance = longToken.balanceOf(msgSender());
        uint shortBalance = shortToken.balanceOf(msgSender());

        if (longBalance > 0){
            uint longPayout = calculate_long_payout(longBalance);
            collateralToken.transfer(msgSender(), longPayout);
            longToken.burnTokens(msgSender(), longBalance);
        }

        if (shortBalance > 0){
            uint shortPayout = calculate_short_payout(shortBalance);
            collateralToken.transfer(msgSender(), shortPayout);
            shortToken.burnTokens(msgSender(), shortBalance);
        }
    }

    function calculate_long_payout(uint longBalance) internal returns (uint longPayout) {
        // Calculates long payout using 8 decimals for the short token value
        uint longTokenValue = outcome.sub(low).mul(TARGET_PRICE_DIGITS).div(high.sub(low));
        uint longPayout = longBalance.mul(longTokenValue).div(TARGET_PRICE_DIGITS);
        
        return longPayout;
    }

    function calculate_short_payout(uint shortBalance) internal returns (uint shortPayout) {
        // Calculates short payout using 8 decimals for the short token value
        uint shortTokenValue = high.sub(outcome).mul(TARGET_PRICE_DIGITS).div(high.sub(low));
        uint shortPayout = shortBalance.mul(shortTokenValue).div(TARGET_PRICE_DIGITS);

        return shortPayout;
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

    function K() public view returns (uint){
        return longToken.balanceOf(address(this)).mul(shortToken.balanceOf(address(this)));
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

        // collateralize the investments, mint the tokens and add in the fees
        uint k = K();
        collateralToken.transferFrom(msgSender(), address(this), investmentAmount);
        fundingToken.issueTokens(address(this), investmentAmountMinusFees);
        balancingToken.issueTokens(address(this), investmentAmountMinusFees);
        feePool = feePool.add(feeAmount);

        // calculate the target balancing quantity
        uint targetBalancingQuantity = k.div(fundingToken.balanceOf(address(this)));
        uint balancingQuantityReturned = balancingToken.balanceOf(address(this)).sub(targetBalancingQuantity).sub(1);

        balancingToken.transfer(msgSender(), balancingQuantityReturned);
    }

    function sell (uint sellAmount, bool long, uint minimumReturnAmount) external{
       
       uint k = K();
       require(longToken.balanceOf(address(this)) * shortToken.balanceOf(address(this)) == k, 'invarint not satisfied');
        if (long){
            longToken.transferFrom(msgSender(), address(this), sellAmount);
        }
        else{
            shortToken.transferFrom(msgSender(), address(this), sellAmount);
        }

        require(sellAmount > 0, 'Sell amount must be greater than 0');
        uint startingLongBalance = longToken.balanceOf(address(this));
        uint startingShortBalance = shortToken.balanceOf(address(this));
        require(startingLongBalance * startingShortBalance > k, 'invarint not satisfied');

        uint a = 1;
        uint b = startingLongBalance.add(startingShortBalance);
        uint c = startingLongBalance.mul(startingShortBalance).sub(k);

        uint burnAmount = solveQuadraticEquation(a, b, c);

        require(startingLongBalance > burnAmount, 'Cannot burn more LONG tokens than existing balance');
        require(startingShortBalance > burnAmount, 'Cannot burn more SHORT tokens than existing balance');
        
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
    
    function solveQuadraticEquation(uint a, uint b, uint c) public returns(uint x){
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