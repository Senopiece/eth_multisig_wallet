pragma solidity >=0.7.6 <0.8.0;

interface ERC20 {
  function totalSupply() external view returns (uint256);
  
  function balanceOf(address who) external view returns (uint256);
  function transfer(address to, uint256 value) external returns (bool);
 
  function allowance(address owner, address spender) external view returns (uint256);
  function transferFrom(address from, address to, uint256 value) external returns (bool);
  function approve(address spender, uint256 value) external returns (bool);
  
  event Transfer(address indexed from, address indexed to, uint256 value);
  event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract Test {
    address[] _owners;
    uint256 _treshhold;
    mapping(bytes32 => address[]) votes; // dabate_id -> addresses, first byte of <id> stores information about type of approval (addOwner/removeOwner etc)
    uint debates_count = 0;
    
    // events //
    
    event ActionConfirmed(bytes32 indexed id, address indexed sender);
    
    event RequestToAddOwner(address indexed newowner);
    event OwnerAdded(address indexed newowner);
    
    event RequestToChangeThreshold(uint256 amount, uint256 oldthresh, uint256 newthresh);
    event ThresholdChanged(uint256 amount, uint256 oldthresh, uint256 newthresh);
    
    event RequestToRemoveOwner(address indexed owner);
    event OwnerRemoved(address indexed owner);
    
    event RequestForTransfer(address indexed token, address indexed receiver, uint256 value);
    event TransferExecuted(address indexed token, address indexed receiver, uint256 value);
    
    event CancelRegistered(bytes32 indexed id, address indexed sender);
    event ActionCanceled(bytes32 indexed id);
    
    // inner //
    
    modifier only_for_owners() {
        bool owned = false;
        for (uint i = 0; i < _owners.length; i++)
        {
            if (_owners[i] == msg.sender)
            {
                owned = true;
                break;
            }
        }
        require(owned, "this method is only for owners, you are not an owner");
        
        _;
    }
    
    function set_treshhold(uint256 value) private {
        emit ThresholdChanged(_owners.length, _treshhold, value);
        _treshhold = value;
    }
    
    function start_new_debate(bytes32 id) private {
        votes[id] = [msg.sender];
        debates_count++;
    }
    
    function stop_debate(bytes32 id) private {
        delete votes[id];
        debates_count--;
    }
    
    // public //
    
    constructor(address[] memory owners, uint256 threshold) {
        // additional conditions
        require(threshold <= owners.length, "threshold should be less or equal to owners amount");
        require(threshold >= 1, "threshold should not be less than 1");
        require(owners.length >= 1, "owners amount should not be less than 1");
        
        // following by the task
        _owners = owners;
        for (uint i = 0; i < _owners.length; i++) {
            emit OwnerAdded(_owners[i]);
        }
        set_treshhold(threshold);
    }
    
    function addOwner(address newowner) public only_for_owners {
        // check if newowner is not already in owners
        for (uint i = 0; i < _owners.length; i++) { require(_owners[i] != newowner, "he is not already in owners"); }
        
        // following by the task description
        bytes32 my_id = keccak256(abi.encodePacked(newowner)) >> 1;
        if (votes[my_id].length != 0)
        {
            for (uint i = 0; i < votes[my_id].length; i++) { require(votes[my_id][i] != msg.sender, "you can't voice twice"); }
            votes[my_id].push(msg.sender);
        }
        else
        {
            start_new_debate(my_id);
            emit RequestToAddOwner(newowner);
        }
        
        emit ActionConfirmed(my_id, msg.sender);
        
        if (votes[my_id].length == _treshhold)
        {
             _owners.push(newowner);
            emit OwnerAdded(newowner);
            
            stop_debate(my_id);
        }
    }
    
    function removeOwner(address owner) public only_for_owners {
        // check if newowner is already in owners
        bool owned = false;
        uint owner_index = 0;
        for (owner_index = 0; owner_index < _owners.length; owner_index++)
        {
            if (_owners[owner_index] == owner)
            {
                owned = true;
                break;
            }
        }
        require(owned, "he is not a owner"); 
        require(_owners.length > 1, "owners amount should be greater than 1");
        
        // following by the task description
        bytes32 my_id = bytes32(0x0100000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(owner)) >> 1);
        if (votes[my_id].length != 0)
        {
            for (uint i = 0; i < votes[my_id].length; i++) { require(votes[my_id][i] != msg.sender, "you can't voice twice"); }
            votes[my_id].push(msg.sender);
        }
        else
        {
            start_new_debate(my_id);
            emit RequestToRemoveOwner(owner);
        }
        
        emit ActionConfirmed(my_id, msg.sender);
        
        if (votes[my_id].length == _treshhold)
        {
            delete _owners[owner_index];
            emit OwnerRemoved(owner);
            
            stop_debate(my_id);
        }
    }
    
    function changeThreshold(uint256 threshold) public only_for_owners {
        // additional conditions
        require(threshold <= _owners.length, "threshold should be less or equal to owners amount");
        require(threshold >= 1, "threshold should not be less than 1");

        // following by the task
        bytes32 my_id = bytes32(0x0200000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(threshold)) >> 1);
        if (votes[my_id].length != 0)
        {
            for (uint i = 0; i < votes[my_id].length; i++) { require(votes[my_id][i] != msg.sender, "you can't voice twice"); }
            votes[my_id].push(msg.sender);
        }
        else
        {
            start_new_debate(my_id);
            emit RequestToChangeThreshold(_owners.length, _treshhold, threshold);
        }
        
        emit ActionConfirmed(my_id, msg.sender);
        
        if (votes[my_id].length == _treshhold)
        {
            uint d = threshold - _treshhold;
                
            require(d >= 0 || debates_count == 1 , "to decrease threshold, previously resolve all the debates in right order");
                
            _treshhold = threshold;
            emit ThresholdChanged(_owners.length, _treshhold - d, _treshhold);

            stop_debate(my_id);
        }
    }
    
    function transfer(address payable receiver, uint256 value) public only_for_owners {
        bytes32 my_id = bytes32(0x0300000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(receiver, value)) >> 1);
        if (votes[my_id].length != 0)
        {
            for (uint i = 0; i < votes[my_id].length; i++) { require(votes[my_id][i] != msg.sender, "you can't voice twice"); }
            votes[my_id].push(msg.sender);
        }
        else
        {
            start_new_debate(my_id);
            emit RequestForTransfer(address(0x0), receiver, value);
        }
        
        emit ActionConfirmed(my_id, msg.sender);
        
        if (votes[my_id].length == _treshhold)
        {
            receiver.transfer(value);
            emit TransferExecuted(address(0x0), receiver, value);
            
            stop_debate(my_id);
        }
    }
    
    function transfer(address token, address receiver, uint256 value) public only_for_owners {
        bytes32 my_id = bytes32(0x0400000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(token, receiver, value)) >> 1);
        if (votes[my_id].length != 0)
        {
            for (uint i = 0; i < votes[my_id].length; i++) { require(votes[my_id][i] != msg.sender, "you can't voice twice"); }
            votes[my_id].push(msg.sender);
        }
        else
        {
            start_new_debate(my_id);
            emit RequestForTransfer(token, receiver, value);
        }
        
        emit ActionConfirmed(my_id, msg.sender);
        
        if (votes[my_id].length == _treshhold)
        {
            require(ERC20(token).transfer(receiver, value), "tokens transfer failed");
            emit TransferExecuted(token, receiver, value);
            
            stop_debate(my_id);
        }
    }
    
    function cancel(bytes32 id) public only_for_owners {
        bool voted = false;
        uint i = 0;
        for (i = 0; i < votes[id].length; i++)
        {
            if (votes[id][i] == msg.sender)
            {
                voted = true;
                break;
            }
        }
        require(voted, "you didn't vote"); 
        
        delete votes[id][i];
        emit CancelRegistered(id, msg.sender);

        if (votes[id].length == 0)
        {
            stop_debate(id);
            emit ActionCanceled(id);
        }
    }
}