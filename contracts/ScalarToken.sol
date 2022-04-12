// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.6;

import {ERC20Upgradeable} from "@openzeppelin-upgradable/contracts/token/ERC20/ERC20Upgradeable.sol";
import {Initializable} from "@openzeppelin-upgradable/contracts/proxy/Initializable.sol";
import {AccessControlUpgradeable} from "@openzeppelin-upgradable/contracts/access/AccessControlUpgradeable.sol";
import {EIP712MetaTransaction} from "./EIP712MetaTransaction.sol";

contract ScalarToken is Initializable, ERC20Upgradeable, AccessControlUpgradeable, EIP712MetaTransaction('ScalarToken', "1")  {

    bytes32 public constant AMM_ROLE = keccak256("AMM_ROLE");

     constructor() public {

    }

    function initialize(string memory name, string memory symbol) public {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        __ERC20_init(name, symbol);
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