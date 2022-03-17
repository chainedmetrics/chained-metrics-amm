pragma solidity ^0.6.6;

import {FixedProductMarketMaker} from './FixedProductMarketMaker.sol';
import  "@openzeppelin/contracts/access/AccessControl.sol";

contract MarketMakerFactory is AccessControl{

    // REPORTING_ROLE allows an address to report on the outcome of a market
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
    // address[] public fpmm_array;

    constructor(address marketCreator) public {
        _setupRole(CREATOR_ROLE, marketCreator);
    }

    function createMarketMaker(string memory tokenName, string memory tokenSymbol, address collateralTokenAddress,
        string memory kpiName, string memory kpiSymbol, uint _high, uint _low, address reportingAddress, uint fee)
        public returns (address){

        require(hasRole(CREATOR_ROLE, msg.sender), "Address does not have REPORTING_ROLE");
        
        FixedProductMarketMaker fpmm = new FixedProductMarketMaker(tokenName, tokenSymbol, collateralTokenAddress,
            kpiName, kpiSymbol, _high, _low, reportingAddress, fee);

        // fpmm_array.push(address(fpmm));
        
    }

}