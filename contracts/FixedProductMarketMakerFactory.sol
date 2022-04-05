// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.6;
pragma experimental ABIEncoderV2;

import {FixedProductMarketMaker, KPIReferenceData} from './FixedProductMarketMaker.sol';
import {ScalarToken} from './ScalarToken.sol';
import  {AccessControl} from "@openzeppelin-contracts/contracts/access/AccessControl.sol";
import {CloneFactory} from './CloneFactory.sol';

// For debugging import hardhat for debugging with console.log("Msg");
// import "hardhat/console.sol";

contract MarketMakerFactory is CloneFactory, AccessControl{

    event MarketCreated(
        address indexed marketAddress,
        address indexed longAddress,
        address indexed shortAddress
    );

    // REPORTING_ROLE allows an address to report on the outcome of a market
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
    FixedProductMarketMaker public fpmm_template;
    ScalarToken public scalar_template;

    address[] public fpmm_array;

    constructor(address marketCreator) public {
        _setupRole(CREATOR_ROLE, marketCreator);
        fpmm_template = new FixedProductMarketMaker();
        scalar_template = new ScalarToken();
    }

    function createMarketMaker(string memory tokenName, string memory tokenSymbol, address collateralAddress,
        address reportingAddress, string memory kpiName, string memory kpiSymbol, uint high, uint low, uint fee)
        public returns (address){

        require(hasRole(CREATOR_ROLE, msg.sender), "Address does not have REPORTING_ROLE");

        string memory longName = string(abi.encodePacked(kpiName, " LONG"));
        string memory longSymbol = string(abi.encodePacked(kpiName, "/L"));
        string memory shortName = string(abi.encodePacked(kpiName, " SHORT"));
        string memory shortSymbol = string(abi.encodePacked(kpiName, "/S"));

        ScalarToken longToken = ScalarToken(createClone(address(scalar_template)));
        ScalarToken shortToken = ScalarToken(createClone(address(scalar_template)));

        longToken.initialize(longName, longSymbol);
        shortToken.initialize(shortName, shortSymbol);

        FixedProductMarketMaker  fpmm = FixedProductMarketMaker(createClone(address(fpmm_template)));
        
        KPIReferenceData memory kpiData;
        kpiData.longAddress = address(longToken);
        kpiData.shortAddress = address(shortToken);
        kpiData.collateralAddress = collateralAddress;
        kpiData.reportingAddress = reportingAddress;
        kpiData.high = high;
        kpiData.low = low;
        kpiData.fee = fee;

        fpmm.initialize(kpiData);
        // console.log("Sender  %s", fpmm.hasRole(fpmm.DEFAULT_ADMIN_ROLE(), msg.sender));
        // console.log("Factory %s", fpmm.hasRole(fpmm.DEFAULT_ADMIN_ROLE(), address(this)));
        longToken.grantRole(longToken.AMM_ROLE(), address(fpmm));
        shortToken.grantRole(shortToken.AMM_ROLE(), address(fpmm));
        longToken.renounceRole(longToken.DEFAULT_ADMIN_ROLE(), address(this));
        shortToken.renounceRole(shortToken.DEFAULT_ADMIN_ROLE(), address(this));
        
        fpmm_array.push(address(fpmm));

        emit MarketCreated(
            address(fpmm), 
            address(longToken), 
            address(shortToken)
        );
    }
}