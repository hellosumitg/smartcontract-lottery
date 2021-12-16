from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config

import time


def deploy_lottery():
    # pass
    # 1st thing we always need is an account to deploy the contract
    # account = get_account(id="freecodecamp-account")
    # Just for checking if we run "brownie run scripts/deploy_lottery.py" after the above code gets saved then we will found much more liberal get_account()
    account = get_account()
    lottery = Lottery.deploy(
        # Similar to our `contructor()` in "Lottery.sol"
        # Now, The way we did that in "Brownie_FundMe" is that we did it in a way where we checked to see if we were on a local chain or not....?
        # If we're on a local chain then we would just pull our addresses directly from our "brownie-config.yaml" file but if weren't on the local chain then we'd...
        # ...deploy some "mocks" and use the address of those "mocks" we're going to do the same thing here...
        # ...but make our lives a little-bit easier by taking the whole process of "Checking" that we're on the local chain or not...
        # ...& "Mocking" into a single function called "get_contract()" and add this function in "helpful_scripts.py"
        get_contract("eth_usd_price_feed").address,  # address _priceFeedAddress
        get_contract("vrf_coordinator").address,  # address _vrfCoordinator
        get_contract("link_token").address,  # address _link
        config["networks"][network.show_active()]["fee"],  # uint256 _fee
        config["networks"][network.show_active()]["keyhash"],  # bytes32 _keyhash
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
        # here `.get(verify", False)` says "get" that "verify key" but if there is no "verify key" there, just default to "false"
    )
    print("Deployed lottery!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # Now we are changing Lottery stage
    starting_tx = lottery.startLottery({"from": account})
    # here we wait for the last transaction to complete otherwise brownie would gets confused at the end
    starting_tx.wait(1)
    print("The lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = (
        lottery.getEntranceFee() + 100000000
    )  # here we take some extra "wei" just to be safe
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # Now before we actually end this lottery we're going to need some "LINK Token" in this particular Contract...
    # ...because if we remember our "endLottery()" calls "requestRandomness(keyhash, fee)" and we can only request...
    # ...some randomness if our contract has somme Chainlink Token associated with it that's why...
    # ...first fund the contract
    # ...and then end the lottery
    # Since funding our contracts with the LINK Token is going to be a pretty common function that we use,...
    # ...so lets move this new function code into the "helpful_scripts.py"
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    # Once we're funded with link then we can go ahead to call "endLottery()" in below code
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # Remember:- When we call this "endlottery()"[i.e in Lottery.sol] we're going to make a request to a `Chainlink Node` and this `Chainlink Node` is going to respond by calling this "fulfillRandomness()"[i.e in Lottery.sol]...
    # ...so we actually have to wait for that Chainlink Node to finish.
    # Now, typically it's within few blocks so normally what we can do is we can just do a "time.sleep(60)"(i.e for 60 sec) and during this time the `Chainlink Node` will have responded so we do "import time"
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()


# Now after running "brownie run scripts/deploy_lottery.py" we get lots of transaction done and after waiting for few seconds our Contract will give "0x0000000000000000000000000000000000000000 is the new winner!"
# this is because there is no `Chainlink Node` that's going to call this "fulfillRandomness()" right now, so for our "Ganache chain" this will hypothetically end with `nothing or zeros` as "winner" as our output...
# ...because there is no `Chainlink Node` actually responding on our local 'Ganache' here.
# for our "Testing" purposes we're going to figure out how to actually get around that and deal with that...
# ...And we want our "Tests" are really solid on a 'development chain' before we actually test this on an actual "Test Net".
# Now, before we get into these "tests" there are couple of things we want to talk about:-
# 1. Integration Test:- Away of testing across multiple complex systems.
# 2. Unit Tests:- A way of testing the smallest pieces of code in an isolated instance/system.
# Typically we like to run our "Unit Tests" exclusively on a development environment and "Integration Tests" on a "Test Net",...
# ...this is really helpful because we can test the majority of our application like we said on a development network and then still be able to see what actually happens on a real "Test Net" and see what happens on "Etherscan" and everything like that...
# ...Typically what people do is inside their "tests" folder create two different folder:-
# 1. unit folder (here we create a file instead of folder naming "test_lottery_unit.py")
# 2. integration folder (here we create a file instead of folder naming "test_lottery_integration.py")

# Now we will deploy the whole contract by running all the functions end to end on a "Test Net"(here Rinkeby) and see what it looks like on "Etherscan" so for this we'll have to run "brownie run scripts/deploy_lottery.py --network rinkeby"
# Now if we jump to "https://rinkeby.etherscan.io/" and paste the "Lottery deployed at: 0x....." address, we'll see Contract with a little check mark is verified and we'll go to the "Read Contract" and we can see all the public variables and public functions
# and when we move to write contract we'll see all the transacting functions that we can interact with... and in the terminal below we can see all the function that get executed.
# Now if we sit on this contract for 60 sec while runniing the above code in in terminal and if we go to "Transactions" section and refresh the page on the website, then we can see we did a contract "creation" we "started the lottery" we "entered the lottery" and we "ended the lottery"
# For checkinig the winner we can see it in the "Contract" section--->by clicking on "Read Contract" section---> and by clicking on the "recentWinner" button and get the address(0x....) of the winner. We can also go to the "Events" section and can see some of the evnts that we had created...
# ...We can see "RequestRandomness" with "[topic0] 0x......" represent this entire event right here. and below this we have a "Hex ->......" which is our first topic which represents our "requestId"
# and also the "OwnershipTransferred" that we got when we actually deployed this contract in the first place.

# Now we had created a working "Smart Contract Lottery with true Provable Randomness" but we want to add an additional piece of file that we're going often to see i.e "conftest.py" in "tests" folder.
# Python automatically knows to look for this "conftest.py" file and we grab different functions from it which we can see in this website:-"https://stackoverflow.com/questions/34466027/in-pytest-what-is-the-use-of-conftest-py-files"
# we skipped this file in this project but we will see this in future projects because it has a lot of really nice testing configuration pieces.

# This is a lot of code and we don't want to write this much amount of code every single time when we are starting from scratch, so now we can do "git-clone" all these repositories right from Chainlink github...
# ...but there's actually very simple way of doing this is with "brownie mixes github" which we have to 'google' and we'll get this "Brownie Mixes Organization" which had a ton of "boilerplate" code for us to go ahead and get started our development...
# ...Now we're going to work with this "Chainlink-mix" folder which we'll fork and get different "contracts", "tests" and many other things to work on(i.e everything that we need to get started) in the next topic...
