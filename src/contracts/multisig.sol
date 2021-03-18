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

    function _addOwner(address addr) internal {
        if (!_is_owner[addr])
        {
            _is_owner[addr] = true;
            _owners_count += 1;
            emit OwnerAdded(addr);
        }
        else
            revert("he is already a owner");
    }

    function _removeOwner(address addr) internal {
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

    function _setThreshold(uint256 value) internal {
        emit ThresholdChanged(countOwners(), _threshold, value);
        _threshold = value;
    }
}

contract MultisigDatapack_3 is MultisigDatapack_2 {
    struct PA {
        address[] confirmators;
        mapping(address => bool) is_confirmed_by;
    }
    mapping(bytes32 => PA) private _pending_actions;

    function isAlreadyConfirmed(bytes32 action_id, address confirmator) public view returns (bool) { // <---------- public
        return _pending_actions[action_id].is_confirmed_by[confirmator];
    }

    function confirmationsCount(bytes32 action_id) public view returns (uint256) { // <---------------------------- public
        return _pending_actions[action_id].confirmators.length;
    }

    function _confirmPendingAction(bytes32 action_id, address confirmator) internal {
        PA storage context = _pending_actions[action_id];
        if (!context.is_confirmed_by[confirmator])
        {
            context.is_confirmed_by[confirmator] = true;
            context.confirmators.push(confirmator);
            emit ActionConfirmed(action_id, confirmator);
        }
        else
            revert("you cannot voice twice");
    }

    function _cancelConfirmation(bytes32 action_id, address confirmator) internal {
        PA storage context = _pending_actions[action_id];
        if (context.is_confirmed_by[confirmator])
        {
            context.is_confirmed_by[confirmator] = false;
            
            for (uint256 i = 0; i < context.confirmators.length; i++)
            {
                if (context.confirmators[i] == confirmator)
                {
                    context.confirmators[i] = context.confirmators[context.confirmators.length - 1];
                    context.confirmators.pop();
                    break;
                }
            }
            
            emit CancelRegistered(action_id, confirmator);
        }
        else
            revert("nothing to cancel");
    }

    function _clearConfirmations(bytes32 action_id) internal {
        PA storage context = _pending_actions[action_id];
        for (uint256 i = 0; i < context.confirmators.length; i++)
        {
            context.is_confirmed_by[context.confirmators[i]] = false;
        }
        delete context.confirmators;
    }
}

contract Multisig is MultisigDatapack_3 {

    mapping(bytes32 => bytes32) sig_to_id;

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
            _addOwner(owners[i]);
        }
        _setThreshold(threshold);
    }

    function addOwner(address newowner) external only_for_owners {
        bytes32 sig = keccak256(abi.encodePacked(newowner));
        bytes32 id = sig_to_id[sig];
        if (confirmationsCount(id) == 0)
        {
            // also here if id = 0 (first appear of such paramerets) ; implicitly we can assume that confirmationsCount(0) = 0

            id = keccak256(abi.encodePacked(sig, block.number));
            sig_to_id[sig] = id;

            emit RequestToAddOwner(newowner);
        }

        if (confirmationsCount(id) + 1 < getThreshold())
        {
            _confirmPendingAction(id, msg.sender); // may revert
        }
        else
        {
            _addOwner(newowner); // may revert

            emit OwnerAdded(newowner);
            emit ActionConfirmed(id, msg.sender);
            _clearConfirmations(id);
        }
    }

    function removeOwner(address owner) external only_for_owners {
        bytes32 sig = keccak256(abi.encodePacked(owner));
        bytes32 id = sig_to_id[sig];
        if (confirmationsCount(id) == 0)
        {
            // also here if id = 0 (first appear of such paramerets) ; implicitly we can assume that confirmationsCount(0) = 0

            id = keccak256(abi.encodePacked(sig, block.number));
            sig_to_id[sig] = id;

            emit RequestToRemoveOwner(owner);
        }

        if (confirmationsCount(id) + 1 < getThreshold())
        {
            _confirmPendingAction(id, msg.sender); // may revert
        }
        else
        {
            require(countOwners() >= 2, "owners amount should not be less than 1");
            require(getThreshold() <= countOwners() - 1, "threshold should be less or equal to owners amount");

            _removeOwner(owner); // may revert

            emit OwnerRemoved(owner);
            emit ActionConfirmed(id, msg.sender);
            _clearConfirmations(id);
        }
    }

    function changeThreshold(uint256 threshold) external only_for_owners {
        bytes32 sig = keccak256(abi.encodePacked(threshold));
        bytes32 id = sig_to_id[sig];
        if (confirmationsCount(id) == 0)
        {
            // also here if id = 0 (first appear of such paramerets) ; implicitly we can assume that confirmationsCount(0) = 0

            id = keccak256(abi.encodePacked(sig, block.number));
            sig_to_id[sig] = id;

            emit RequestToChangeThreshold(countOwners(), getThreshold(), threshold);
        }

        if (confirmationsCount(id) + 1 < getThreshold())
        {
            _confirmPendingAction(id, msg.sender); // may revert
        }
        else
        {
            require(threshold <= countOwners(), "threshold should be less or equal to owners amount");

            uint256 oldth = getThreshold();
            _setThreshold(threshold);

            emit ThresholdChanged(countOwners(), oldth, threshold);
            emit ActionConfirmed(id, msg.sender);
            _clearConfirmations(id);
        }
    }

    function transfer(address payable receiver, uint256 value) external only_for_owners {
        bytes32 sig = keccak256(abi.encodePacked(receiver, value));
        bytes32 id = sig_to_id[sig];
        if (confirmationsCount(id) == 0)
        {
            // also here if id = 0 (first appear of such paramerets) ; implicitly we can assume that confirmationsCount(0) = 0

            id = keccak256(abi.encodePacked(sig, block.number));
            sig_to_id[sig] = id;

            emit RequestForTransfer(address(0x0), receiver, value);
        }

        if (confirmationsCount(id) + 1 < getThreshold())
        {
            _confirmPendingAction(id, msg.sender); // may revert
        }
        else
        {
            receiver.transfer(value); // may revert

            emit TransferExecuted(address(0x0), receiver, value);
            emit ActionConfirmed(id, msg.sender);
            _clearConfirmations(id);
        }
    }

    function transfer(address token, address receiver, uint256 value) external only_for_owners {
        bytes32 sig = keccak256(abi.encodePacked(token, receiver, value));
        bytes32 id = sig_to_id[sig];
        if (confirmationsCount(id) == 0)
        {
            // also here if id = 0 (first appear of such paramerets) ; implicitly we can assume that confirmationsCount(0) = 0

            id = keccak256(abi.encodePacked(sig, block.number));
            sig_to_id[sig] = id;

            emit RequestForTransfer(token, receiver, value);
        }

        if (confirmationsCount(id) + 1 < getThreshold())
        {
            _confirmPendingAction(id, msg.sender); // may revert
        }
        else
        {
            ERC20(token).transfer(receiver, value); // may revert

            emit TransferExecuted(token, receiver, value);
            emit ActionConfirmed(id, msg.sender);
            _clearConfirmations(id);
        }
    }

    function cancel(bytes32 id) external only_for_owners {
        _cancelConfirmation(id, msg.sender);
        if (confirmationsCount(id) == 0)
        {
            emit ActionCanceled(id);
        }
    }

    // make him availeble to recieve ethers
    fallback() external payable {}
}