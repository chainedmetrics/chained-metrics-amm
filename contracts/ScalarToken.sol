// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.6;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import  "@openzeppelin/contracts/access/AccessControl.sol";
import {EIP712MetaTransaction} from "./EIP712MetaTransaction.sol";

contract ScalarToken is ERC20, AccessControl, EIP712MetaTransaction('ScalarToken', "1")  {

    bytes32 public constant AMM_ROLE = keccak256("AMM_ROLE");
       
    constructor(string memory tokenName, string memory tokenSymbol) ERC20(tokenName,  tokenSymbol) public {
        _setupRole(AMM_ROLE, msgSender());
    }

    function burnTokens(address _address, uint256 amount) public {
        require(hasRole(AMM_ROLE, msgSender()), "This contract does not have permissions to burn tokens");
        require(amount <= balanceOf(_address), "You do not have enough tokens to burn");
        _burn(_address, amount);       

    }
    
    function issueTokens(address reciever, uint256 amount) public{

        require(hasRole(AMM_ROLE, msgSender()), "This contract does not have permissions to issueTokens tokens");
         _mint(reciever, amount);
    }
}