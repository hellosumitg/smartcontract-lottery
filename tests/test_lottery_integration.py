"""
Here we will do one test for this 'Integration Test' but keep in mind we would have to test every piece of our code in real projects... 
"""

from brownie import network  # network here is Rinkeby
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)
from scripts.deploy_lottery import deploy_lottery
import time


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # we can add above +100 or +1000 in with "lottery.getEntranceFee() + 100}" as shown...
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # here it could be little bit different from our "Unit Test/ test_lottery_unit.py" because in that we pretended that we were the "VRFCoordinator"
    # and we called the callBackWithRandomness() as we were a "Chainlink Node" as shown below:-
    """
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    """
    # but here we're on an actual network so we're actually just going to wait for that Chainlink Node to respond so for simplicity we just do as shown in below code...
    time.sleep(60)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


# Now for testing till here, we will run "brownie test -k test_can_pick_winner --network rinkeby -s" using '-s' will print out whatever brownie is going to be printing out to make everything a little bit more verbose here...
# ...and before running just check that we have `Rinkeby TestNet ETH` and `Rinkeby LINK ETH` if not collect from here "https://docs.chain.link/docs/vrf-contracts/" in our 'metamask wallet' similar as we did in "Kovan" and its passing well...
# Now we've added all our `tests` what we can do run a complete test bu running "brownie test" this will run through all of our development tests here we'll see it'll go really quickly and we can see how much faster it is for us to run our test on a "Local Chain"
