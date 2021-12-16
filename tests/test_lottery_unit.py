"""
While writing `Unit Tests` we really want to test hypothetically every single line of code in our `smart contracts` this is incredibly important of course because `smart contracts` are open to everybody to see and interact with.
"""


# Price of 1 ETH = $ 4426.70 at the time of coding
# 0.011
# 110000000000000000

from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)

from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery  # importing `deploy_lottery()`
from web3 import Web3
import pytest

# function to test entrance fee
"""def test_get_entrance_fee():  # In order to deploy this we need to get an account
    account = accounts[0]  # Taking account from brownie
    lottery = Lottery.deploy(
        config["networks"][network.show_active()]["eth_usd_price_feed"],
        {"from": account},
    )
    # We know below codes are not the best way to test our contracts but it can be a nice sanity check
    # assert lottery.getEntranceFee() > Web3.toWei(0.010, "ether")
    # assert lottery.getEntranceFee() < Web3.toWei(0.014, "ether")
    # As we had know in the last section we made "mainnet-fork-dev" network which is present till now in the "brownie networks list--> Develpoment section",...
    # ...Now we're going to customize our new "mainnet-fork" network for testing and for that we have to delete the brownie's internal built-in "mainnet-fork" and for this we have to run...
    # ..."brownie networks delete mainnet-fork" and add our own "mainnet-fork" as our ethereum connection by creating new app naming "smartcontract-lottery" in "Alchemy" and copy the "http...",
    # ...after that we have to run this command...
    # ..."brownie networks add development mainnet-fork cmd=ganache-cli host=http://127.0.0.1 fork=https://eth-mainnet.alchemyapi.io/v2/j20pNEfQJS9beSertXhB8w9UdjvTXznF accounts=10 mnemonic=brownie port=8545"
"""


def test_get_entrance_fee():
    # Since, this is a `Unit Test` we only want to run this when we're working on a `LOCAL_BLOCKCHAIN_ENVIRONMENTS` or `LOCAL_DEVELOPMENT_NETWORKS`
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2,000 eth / usd feed
    # usdEntryFee is 50
    # 2000/1 == 50/x == 0.025
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrance_fee == entrance_fee


# Now for testing till here, we will run "brownie test -k test_get_entrance_fee" and this passing well.
# After including `LOCAL_BLOCKCHAIN_ENVIRONMENTS` for testing code till here we will run "brownie test -k test_get_entrance_fee --network rinkeby" then it should go ahead and skip this.


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


# Now for testing till here, we will run "brownie test -k test_cant_enter_unless_started" and this passing as well.


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account
    # because we have our players array in "address payable[] public players;" in "contract Lottery is VRFConsumerBase, Ownable {...}" at "Lottery.sol"
    # and we're going to assert that we're pushing them onto our array correctly.


# Now for testing till here, we will run "brownie test -k test_can_start_and_enter_lottery" and this passing as well.


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # If we look back in "Lottery.sol" contract when we call "endLottery()", we're not really doing a whole lot of thing but just changing our state so we're just checking to see if our `CALCULATING_WINNER` state is different...
    """enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }"""
    # We can see that `CALCULATING_WINNER` is at index position `2` so checking the same in below code...
    assert lottery.lottery_state() == 2


# Now for testing till here, we will run "brownie test -k test_can_end_lottery" and this passing as well.

# Now we will do the most interesting piece of this entire `Lottery.sol` contract we're going to test whether or not our `fulfillRandomness()` actually works correctly i.e
# 1. does it corectly `choose` a winner ?
# 2. does it corectly `pay` a winner ?
# 3. does it corectly `reset` ?
# This "Unit Test" is drastically close to being an "Integration Test" but as we said we'll be little loose with the definitions here...
def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Now doing the same above step for multiple different accounts as well...
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    # Now we're going to choose the winner, and for this we have to call "fulfillRandomness()" so as to test line-by-line the "fulfillRandomness()" of our "Lottery.sol" contract...
    # ...Now if we llok at our "VRFCoordinatorMock.sol" contract, we have the function called "callBackWithRandomness" i.e...
    """
    function callBackWithRandomness(
        bytes32 requestId,
        uint256 randomness,
        address consumerContract
    ) public {
        VRFConsumerBase v;
        bytes memory resp = abi.encodeWithSelector(
            v.rawFulfillRandomness.selector,
            requestId,
            randomness
        );
        uint256 b = 206000;
        require(gasleft() >= b, "not enough gas for consumer");
        (bool success, ) = consumerContract.call(resp);
    }
    """
    # and this "callBackWithRandomness()" calls the "rawFulfillRandomness.selector" which eventually will call that "fulfillRandomness()" function but this is the entry point that the node actually calls,...
    # ...we have to pretend to be a `Chainlink Node` and call "callBackWithRandomness()", we're going to return a `random number`, of course we have to choose the contract we want to return to...
    # ...but we also have to pass the original `requestId` associated with the original call. Now, in our "Lottery .sol" contract our `endLottrey()` isn't going to return anything and...
    # ...even if it did it would be really difficult for us to get that return type in our `python`. So, what we want to do is to keep track of when this contract actually entered the "CALCULATING_WINNER" stage...
    # ...is we want to do, what's called emitting an "Event" see here for detailed description:-"https://docs.soliditylang.org/en/develop/contracts.html?highlight=events#events"
    # but for now, "Events" are pieces of data executed and stored in the Blockchain but are not accessible by any "smart contracts", we can think them as the print lines/statements of a Blockchain.
    # Events are much more gas efficient that using a storage variable.
    # Lets say when we see "Transaction's-->Logs section" in the Rinkeby Etherscan website i.e. "https://rinkeby.etherscan.io/tx/0x86c5d0f0a3bb53bcbe760d04f0fc2c9e617bd0b383adf13d04a23f12ea7ec4f2#eventlog" which includes all the different events.
    # Now there's a lot of information here so we're actually going to do an event ourself just so that we can see what this really looks like, SO we can see on the above linked website that when we call the "endLottery()" funtion of "Lottery.sol" contract,...
    # ...then in the logs when we scroll down to the bottom there's an event here called "RandomnessRequest()" which was spit out by "VRFCoordinatorMock.sol" contract and also spit out by the "VRFConsumerBase.sol" contract that we inherited,...
    # ..,it even has some data that's already been decoded, one of those pieces of data is "requestId".
    # Now to add and event we first need to create our event type at the top in "Lottery.sol" contract which is "event RequestedRandomness(bytes32 requestId);"
    # Now that we have this event being "emitted" in our "Lottery.sol" contract in "endLottery()" at "emit RequestedRandomness(requestId);" back in this test when we call "endLottery()", it will actually "emit" one of these events to our transaction, So we can say that as follows:-
    starting_balance_of_account = (
        account.balance()
    )  # for making sure that the "recentWinner's" account gets more money
    balance_of_lottery = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"][
        "requestId"
    ]  # Inside this "transaction" object is actually an attribute called "events" which stores all of our "events" and then we look for "RequestedRandomness" event and find its "requestId"
    # these "events" are going to be very helpful for writing tests these events are also very helpful for a number of other reasons one of the big ones is:-
    # Upgrading our smart contracts or understanding when a mapping is updated, but for now we're going to be usng them for testing. Now we have this "requestId" what we can do is pretend to be the `Chainlink Node` and use this "callBackWithRandomness()"...
    # ...to dummy getting a random number back from Chainlink Node so for this we're going to call "get_contract()" as shown in below code...
    STATIC_RNG = 777  # STATIC_RNG is some random number
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    # 777 % 3 = 0
    assert (
        lottery.recentWinner() == account
    )  # because we set "recentWinner" and trtansfer them some money in "Lottery.sol" contract
    assert (
        lottery.balance() == 0
    )  # because we are transfering all the money to the "recentWinner's" account in above line of code.
    assert account.balance() == starting_balance_of_account + balance_of_lottery


# Now for testing till here, we will run "brownie test -k test_can_pick_winner_correctly" and this passing as well.
# Now lets move to our "test_lottery_integration.py" so that we can run the contract on actual chain....
