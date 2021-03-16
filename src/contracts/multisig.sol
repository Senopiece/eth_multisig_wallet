pragma solidity >=0.7.4 <=0.7.6;

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

contract MultisigEvents {
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
}

contract MultisigDatapack_1 is MultisigEvents {
    uint256 private _owners_count;
    mapping(address => bool) private _is_owner;

    function countOwners() public view returns (uint256) { // <---------------------------------------------------- public
        return _owners_count;
    }

    function isOwner(address addr) public view returns (bool) { // <----------------------------------------------- public
        return _is_owner[addr];
    }

    function addOwner(address addr) internal {
        if (!_is_owner[addr])
        {
            _is_owner[addr] = true;
            _owners_count += 1;
            emit OwnerAdded(addr);
        }
        else
            revert("he is already a owner");
    }

    function removeOwner(address addr) internal {
        if (_is_owner[addr])
        {
            _is_owner[addr] = false;
            _owners_count -= 1;
            emit OwnerRemoved(addr);
        }
        else
            revert("he is not a owner");
    }
}

contract MultisigDatapack_2 is MultisigDatapack_1 {
    uint256 private _threshold;

    function getThreshold() public view returns (uint256) { // <--------------------------------------------------- public
        return _threshold;
    }

    function setThreshold(uint256 value) internal {
        emit ThresholdChanged(countOwners(), _threshold, value);
        _threshold = value;
    }
}

contract MultisigDatapack_3 is MultisigDatapack_2 {
    struct PA {
        uint256 confirmations_count;
        mapping(address => bool) is_confirmed_by;
    }
    mapping(bytes32 => PA) private _pending_actions;

    function isAlreadyConfirmed(bytes32 action_id, address confirmator) public view returns (bool) { // <---------- public
        return _pending_actions[action_id].is_confirmed_by[confirmator];
    }

    function confirmationsCount(bytes32 action_id) public view returns (uint256) { // <---------------------------- public
        return _pending_actions[action_id].confirmations_count;
    }

    function confirmPendingAction(bytes32 action_id, address confirmator) internal {
        if (!_pending_actions[action_id].is_confirmed_by[confirmator])
        {
            _pending_actions[action_id].is_confirmed_by[confirmator] = true;
            emit ActionConfirmed(action_id, confirmator);
        }
        else
            revert("you cannot voice twice");
    }

    function cancelConfirmation(bytes32 action_id, address confirmator) internal {
        if (_pending_actions[action_id].is_confirmed_by[confirmator])
        {
            _pending_actions[action_id].is_confirmed_by[confirmator] = false;
            emit CancelRegistered(action_id, confirmator);
        }
        else
            revert("nothing to cancel");
    }

    function clearConfirmations(bytes32 action_id) internal {
        _pending_actions[action_id] = PA();
    }
}

contract Multisig is MultisigDatapack_3 {

    modifier only_for_owners() {
        require(isOwner(msg.sender), "this method is only for owners, you are not an owner");

        _;
    }

// public methods

    constructor(address[] memory owners, uint256 threshold) {
        // additional conditions
        require(threshold <= owners.length, "threshold should be less or equal to owners amount");
        require(threshold >= 1, "threshold should not be less than 1");
        require(owners.length >= 1, "owners amount should not be less than 1");

        // following by the task
        for (uint256 i = 0; i < owners.length; i++) {
            addOwner(owners[i]);
        }
        setThreshold(threshold);
    }

    function addOwner(address newowner) public only_for_owners {
        bytes32 id = keccak256(abi.encodePacked(newowner)) >> 1;
        // TODO
    }

    function removeOwner(address owner) public only_for_owners {
        bytes32 id = bytes32(0x0100000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(owner)) >> 1);
        // TODO
    }

    function changeThreshold(uint256 threshold) public only_for_owners {
        bytes32 id = bytes32(0x0200000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(threshold)) >> 1);
        // TODO
    }

    function transfer(address payable receiver, uint256 value) public only_for_owners {
        bytes32 id = bytes32(0x0300000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(receiver, value)) >> 1);
        // TODO
    }

    function transfer(address token, address receiver, uint256 value) public only_for_owners {
        bytes32 id = bytes32(0x0400000000000000000000000000000000000000000000000000000000000000) | (keccak256(abi.encodePacked(token, receiver, value)) >> 1);
        // TODO
    }

    function cancel(bytes32 id) public only_for_owners {
        // TODO
    }
}