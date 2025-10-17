// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract UmanityToken is ERC20, Ownable, Pausable {
    // Token configuration - Updated Economics
    uint256 public constant MAX_SUPPLY = 10_000_000_000 * 10**18; // 10 billion tokens
    uint256 public constant DONOR_REWARDS_ALLOCATION = 4_000_000_000 * 10**18; // 40% for donor rewards
    
    // Distribution tracking
    uint256 public donorRewardsMinted;
    
    // Authorized minters (donation contracts)
    mapping(address => bool) public authorizedMinters;
    
    // Events
    event MinterAuthorized(address indexed minter);
    event MinterRevoked(address indexed minter);
    event DonorRewardsMinted(address indexed to, uint256 amount);
    
    constructor() ERC20("Umanity", "UMAN") {
        // Professional Distribution (60% of supply minted at launch)
        
        // Team (15% with vesting) = 1.5B tokens
        _mint(msg.sender, 1_500_000_000 * 10**18);
        
        // Community/Ecosystem (20%) = 2B tokens  
        _mint(msg.sender, 2_000_000_000 * 10**18);
        
        // Operational (25% - marketing, treasury, liquidity) = 2.5B tokens
        _mint(msg.sender, 2_500_000_000 * 10**18);
        
        // Note: 40% (4B tokens) reserved for donor rewards via minting
    }
    
    // Authorize a contract to mint donor reward tokens
    function authorizeMinter(address _minter) external onlyOwner {
        require(_minter != address(0), "Invalid minter address");
        authorizedMinters[_minter] = true;
        emit MinterAuthorized(_minter);
    }
    
    // Revoke minting authorization
    function revokeMinter(address _minter) external onlyOwner {
        authorizedMinters[_minter] = false;
        emit MinterRevoked(_minter);
    }
    
    // Mint donor reward tokens (only authorized contracts)
    function mint(address to, uint256 amount) external {
        require(authorizedMinters[msg.sender], "Not authorized to mint");
        require(to != address(0), "Cannot mint to zero address");
        require(donorRewardsMinted + amount <= DONOR_REWARDS_ALLOCATION, "Exceeds donor allocation");
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds maximum supply");
        
        donorRewardsMinted += amount;
        _mint(to, amount);
        
        emit DonorRewardsMinted(to, amount);
    }
    
    // Get remaining donor reward tokens available for minting
    function remainingDonorRewards() external view returns (uint256) {
        return DONOR_REWARDS_ALLOCATION - donorRewardsMinted;
    }
    
    // Pause token transfers (emergency only)
    function pause() external onlyOwner {
        _pause();
    }
    
    // Unpause token transfers
    function unpause() external onlyOwner {
        _unpause();
    }
    
    // Override transfer functions to add pause functionality
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override {
        super._beforeTokenTransfer(from, to, amount);
        require(!paused(), "Token transfers are paused");
    }
    
    // Get token distribution info
    function getDistributionInfo() external view returns (
        uint256 maxSupply,
        uint256 currentSupply,
        uint256 donorAllocation,
        uint256 donorMintedAmount,
        uint256 donorRemaining
    ) {
        return (
            MAX_SUPPLY,
            totalSupply(),
            DONOR_REWARDS_ALLOCATION,
            donorRewardsMinted,
            DONOR_REWARDS_ALLOCATION - donorRewardsMinted
        );
    }
}