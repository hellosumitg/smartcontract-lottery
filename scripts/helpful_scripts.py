from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

# below function code taken from the last project
def get_account(index=None, id=None):
    # accounts[0] : as we have a way to use brownie ganache account
    # accounts.add("env") : as we have a way to use our environment variables
    # accounts.load("id") :
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    # below code is for local blockchain checking
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    # If nothing that we define prior to below code then the below code will just default to grab right from our "brownie-config.yaml" file
    return accounts.add(config["wallets"]["from_key"])
    # and run "brownie accounts list" to check


# Craeting mappings of "contract_name" to their "type"
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,  # this means that anytime we see "eth_usd_price_feed" we know that, that's going to be a "MockV3Aggregator" if we need to deploy a mock.
    "vrf_coordinator": VRFCoordinatorMock,  # this means that anytime we see "vrf_coordinator" we know that, that's going to be a "VRFCoordinatorMock" if we need to deploy a mock.
    "link_token": LinkToken,  # this means that anytime we see "link_token" we know that, that's going to be a "LinkToken" if we need to deploy a mock.
}


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract, and
    return that mock contract.
        Args:
            contract_name (string)
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            version of this contract.
            # for example if we have a MockV3Aggregator Contract then it will do the most recent version of that i.e...
            MockV3Aggregator[-1]
    If this is confusing then we will go to Chainlink Mix (i.e "https://github.com/smartcontractkit/chainlink-mix/blob/master/scripts/helpful_scripts.py")
    and this has a more robust description of what's going on in this "get_contract()"
    """
    contract_type = contract_to_mock[contract_name]
    # Now we need to check that do we actually even need to deploy a "Mock" and we'll skip the "FORKED_LOCAL_ENVIRONMENTS" because again we don't need to deploy a "Mock price_feed address" on a "FORKED_LOCAL_ENVIRONMENTS"
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            # above is equivalent to doing something like "MockV3Aggregator.length". We're cchecking how many "MockV3Aggregators" have actually been deployed, if none have been deployed we're going ahead and deploy them
            deploy_mocks()
        # NOw we'er going to get that deployed "Mock" Contract i.e similar like grabbing recently deployed MockV3Aggregator (or "MockV3Aggregator[-1]")
        contract = contract_type[-1]

    # Above part will work perfetly for our Development Context but however we're not alway's going to just want to deploy to a development network we'er also going to want to deploy to testnets. So then we'll say "else"
    # and in this way we just grab that contract from the running config for example
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # address
        # ABI
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        # MockV3Aggregator.abi
    return contract


DECIMALS = 8
INITIAL_VALUE = 200000000000


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Deployed!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):
    # amount = 0.1 LINK or 100000000000000000
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    # Other way to "transfer" LINK Token directly on the Contract, is by this using the "interfaces folder" to actually interact with some contracts
    # Right now we have our "Mock" `LinkToken.sol` in here which have all the definations and functionalities in it.
    # May be we only have the interface maybe we only have some of the function definitions
    # So we can still interact with contracts with just an interface because interface will compile down to our "ABI"
    # So as another way of teaching us how to actually work with some of these contracts, is we can use the "LinkTokenInterface()"
    # below is the Another way which we can actually create contracts to actually interact with them as we talk in just above comment lines.

    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})

    tx.wait(1)
    print("Fund contract!")
    return tx

    # Till now we've probably strating to see that Brownie has a lot of built-in tools that make it really easy for us to interact with contracts.
    # If we have the ABI we can just pop it into contract using "Contract.from_abi()" with address and ABI...
    # ..but if we have interface we don't even need to compile down to the ABI ourselves because brownie is smart enough to know that it can compile down to ABI itself
    # and we can just work directly with that interface which is incredibly powerful.
