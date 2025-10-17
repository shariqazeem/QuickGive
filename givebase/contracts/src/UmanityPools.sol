// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract UmanityPools is Ownable, ReentrancyGuard, Pausable {
    
    // Pool structure - matches your Django model
    struct Pool {
        string name;
        string poolType;  // emergency, community, creators, development
        string description;
        string emoji;
        uint256 totalRaised;
        uint256 totalDistributed;
        uint256 donorCount;
        uint256 allocationPercentage;  // 0-100
        bool isActive;
        address payable withdrawalAddress;  // Where to send funds
        uint256 createdAt;
    }
    
    // Donation record for tracking
    struct DonationRecord {
        address donor;
        uint256 poolId;
        uint256 amount;
        uint256 pointsEarned;
        uint256 timestamp;
        string txHash;
    }
    
    // State variables
    mapping(uint256 => Pool) public pools;
    mapping(address => mapping(uint256 => uint256)) public userPoolDonations;
    mapping(address => uint256) public userTotalDonated;
    mapping(address => uint256) public userTotalPoints;
    mapping(address => uint256) public userDonationCount;
    mapping(string => bool) public processedTransactions; // Prevent duplicates
    
    uint256 public nextPoolId = 1;  // Start from 1 to match Django
    uint256 public totalDonated;
    uint256 public totalDonors;
    uint256 public activePools;
    
    // Configuration
    uint256 public constant POINTS_PER_ETH = 1_000_000;  // 1 ETH = 1M points
    uint256 public minDonation = 0.0001 ether;  // Adjustable minimum
    uint256 public maxDonation = 100 ether;      // Safety limit
    
    // Events
    event PoolCreated(
        uint256 indexed poolId,
        string name,
        string poolType,
        uint256 allocationPercentage
    );
    
    event PoolUpdated(
        uint256 indexed poolId,
        bool isActive
    );
    
    event DonationMade(
        address indexed donor,
        uint256 indexed poolId,
        uint256 amount,
        uint256 pointsEarned,
        string txHash
    );
    
    event FundsWithdrawn(
        uint256 indexed poolId,
        address indexed to,
        uint256 amount
    );
    
    event EmergencyWithdrawal(
        address indexed to,
        uint256 amount
    );
    
    event MinDonationUpdated(uint256 newMinimum);
    event MaxDonationUpdated(uint256 newMaximum);
    
    constructor() {
        // Initialize default pools to match your Django setup
        _createPool(
            "Emergency Fund",
            "emergency",
            "Help those in urgent need worldwide",
            unicode"🚨",
            25,
            payable(msg.sender)  // Cast to address payable
        );
        
        _createPool(
            "Community Projects",
            "community",
            "Fund community initiatives",
            unicode"🏘️",
            30,
            payable(msg.sender)  // Cast to address payable
        );
        
        _createPool(
            "Creator Support",
            "creators",
            "Support content creators",
            unicode"🎨",
            20,
            payable(msg.sender)  // Cast to address payable
        );
        
        _createPool(
            "Platform Development",
            "development",
            "Improve Umanity platform",
            unicode"⚡",
            25,
            payable(msg.sender)  // Cast to address payable
        );
    }
    
    // Internal function to create pools
    function _createPool(
        string memory _name,
        string memory _poolType,
        string memory _description,
        string memory _emoji,
        uint256 _allocationPercentage,
        address payable _withdrawalAddress
    ) internal returns (uint256) {
        uint256 poolId = nextPoolId++;
        
        pools[poolId] = Pool({
            name: _name,
            poolType: _poolType,
            description: _description,
            emoji: _emoji,
            totalRaised: 0,
            totalDistributed: 0,
            donorCount: 0,
            allocationPercentage: _allocationPercentage,
            isActive: true,
            withdrawalAddress: _withdrawalAddress,
            createdAt: block.timestamp
        });
        
        activePools++;
        
        emit PoolCreated(poolId, _name, _poolType, _allocationPercentage);
        return poolId;
    }
    
    // Public function to create new pools (admin only)
    function createPool(
        string memory _name,
        string memory _poolType,
        string memory _description,
        string memory _emoji,
        uint256 _allocationPercentage,
        address payable _withdrawalAddress
    ) external onlyOwner returns (uint256) {
        require(_allocationPercentage <= 100, "Allocation cannot exceed 100%");
        require(_withdrawalAddress != address(0), "Invalid withdrawal address");
        
        return _createPool(
            _name,
            _poolType,
            _description,
            _emoji,
            _allocationPercentage,
            _withdrawalAddress
        );
    }
    
    // Update pool status
    function updatePoolStatus(uint256 _poolId, bool _isActive) external onlyOwner {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        
        if (pools[_poolId].isActive && !_isActive) {
            activePools--;
        } else if (!pools[_poolId].isActive && _isActive) {
            activePools++;
        }
        
        pools[_poolId].isActive = _isActive;
        emit PoolUpdated(_poolId, _isActive);
    }
    
    // Update pool details
    function updatePoolDetails(
        uint256 _poolId,
        string memory _description,
        uint256 _allocationPercentage
    ) external onlyOwner {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        require(_allocationPercentage <= 100, "Allocation cannot exceed 100%");
        
        pools[_poolId].description = _description;
        pools[_poolId].allocationPercentage = _allocationPercentage;
    }
    
    // Update withdrawal address for a pool
    function updatePoolWithdrawalAddress(
        uint256 _poolId,
        address payable _newAddress
    ) external onlyOwner {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        require(_newAddress != address(0), "Invalid address");
        
        pools[_poolId].withdrawalAddress = _newAddress;
    }
    
    // Main donation function
    function donateToPool(uint256 _poolId) external payable nonReentrant whenNotPaused {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        require(pools[_poolId].isActive, "Pool is not active");
        require(msg.value >= minDonation, "Below minimum donation");
        require(msg.value <= maxDonation, "Exceeds maximum donation");
        
        Pool storage pool = pools[_poolId];
        
        // Calculate points (1 ETH = 1,000,000 points)
        uint256 pointsEarned = (msg.value * POINTS_PER_ETH) / 1 ether;
        
        // Update pool stats
        pool.totalRaised += msg.value;
        
        // Track unique donors
        if (userPoolDonations[msg.sender][_poolId] == 0) {
            pool.donorCount++;
        }
        
        // Update user stats
        if (userTotalDonated[msg.sender] == 0) {
            totalDonors++;
        }
        
        userPoolDonations[msg.sender][_poolId] += msg.value;
        userTotalDonated[msg.sender] += msg.value;
        userTotalPoints[msg.sender] += pointsEarned;
        userDonationCount[msg.sender]++;
        
        // Update global stats
        totalDonated += msg.value;
        
        // Generate a pseudo tx hash for the event (in real scenario, use actual tx hash)
        string memory txHash = string(abi.encodePacked("0x", toHexString(uint256(keccak256(abi.encodePacked(msg.sender, _poolId, msg.value, block.timestamp))))));
        
        emit DonationMade(msg.sender, _poolId, msg.value, pointsEarned, txHash);
    }
    
    // Withdraw funds from specific pool
    function withdrawFromPool(
        uint256 _poolId,
        uint256 _amount
    ) external onlyOwner nonReentrant {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        Pool storage pool = pools[_poolId];
        require(_amount <= pool.totalRaised - pool.totalDistributed, "Insufficient pool balance");
        
        pool.totalDistributed += _amount;
        pool.withdrawalAddress.transfer(_amount);
        
        emit FundsWithdrawn(_poolId, pool.withdrawalAddress, _amount);
    }
    
    // Withdraw to specific address (emergency or specific needs)
    function withdrawToAddress(
        uint256 _poolId,
        address payable _to,
        uint256 _amount
    ) external onlyOwner nonReentrant {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        require(_to != address(0), "Invalid recipient address");
        Pool storage pool = pools[_poolId];
        require(_amount <= pool.totalRaised - pool.totalDistributed, "Insufficient pool balance");
        
        pool.totalDistributed += _amount;
        _to.transfer(_amount);
        
        emit FundsWithdrawn(_poolId, _to, _amount);
    }
    
    // Emergency withdraw all funds
    function emergencyWithdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        payable(owner()).transfer(balance);
        emit EmergencyWithdrawal(owner(), balance);
    }
    
    // Get pool balance (undistributed funds)
    function getPoolBalance(uint256 _poolId) external view returns (uint256) {
        require(_poolId > 0 && _poolId < nextPoolId, "Invalid pool ID");
        return pools[_poolId].totalRaised - pools[_poolId].totalDistributed;
    }
    
    // Get user stats
    function getUserStats(address _user) external view returns (
        uint256 totalDonatedAmount,
        uint256 totalPoints,
        uint256 donationCount
    ) {
        return (
            userTotalDonated[_user],
            userTotalPoints[_user],
            userDonationCount[_user]
        );
    }
    
    // Get platform stats
    function getPlatformStats() external view returns (
        uint256 _totalDonated,
        uint256 _totalDonors,
        uint256 _activePools,
        uint256 _totalPools
    ) {
        return (
            totalDonated,
            totalDonors,
            activePools,
            nextPoolId - 1
        );
    }
    
    // Get all pools info
    function getAllPools() external view returns (
        uint256[] memory ids,
        string[] memory names,
        uint256[] memory raised,
        bool[] memory active
    ) {
        uint256 totalPools = nextPoolId - 1;
        ids = new uint256[](totalPools);
        names = new string[](totalPools);
        raised = new uint256[](totalPools);
        active = new bool[](totalPools);
        
        for (uint256 i = 1; i <= totalPools; i++) {
            ids[i-1] = i;
            names[i-1] = pools[i].name;
            raised[i-1] = pools[i].totalRaised;
            active[i-1] = pools[i].isActive;
        }
        
        return (ids, names, raised, active);
    }
    
    // Admin functions
    function setMinDonation(uint256 _minDonation) external onlyOwner {
        minDonation = _minDonation;
        emit MinDonationUpdated(_minDonation);
    }
    
    function setMaxDonation(uint256 _maxDonation) external onlyOwner {
        maxDonation = _maxDonation;
        emit MaxDonationUpdated(_maxDonation);
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    // Utility function to convert uint to hex string
    function toHexString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }
        uint256 temp = value;
        uint256 length = 0;
        while (temp != 0) {
            length++;
            temp >>= 8;
        }
        bytes memory buffer = new bytes(2 * length);
        while (value != 0) {
            length -= 1;
            buffer[2 * length + 1] = bytes1(uint8(48 + uint256(value & 0x0f)));
            value >>= 4;
            buffer[2 * length] = bytes1(uint8(48 + uint256((value & 0x0f) > 9 ? 87 : 48) + uint256(value & 0x0f)));
            value >>= 4;
        }
        return string(buffer);
    }
    
    // Receive function to accept direct ETH transfers
    receive() external payable {
        revert("Direct transfers not allowed. Use donateToPool function.");
    }
    
    fallback() external payable {
        revert("Direct transfers not allowed. Use donateToPool function.");
    }
}