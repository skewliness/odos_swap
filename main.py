import os, signal, threading, wx, time, random
from web3 import Web3, constants
from pubsub import pub


class Myapp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.frame = wx.Frame(parent=None, title='odos刷交易  合作VX：Fooyao', size=(474, 450), name='frame', style=541072384)
        self.startWindow = wx.Panel(self.frame)
        self.frame.Centre()
        self.multiText = wx.TextCtrl(self.startWindow, size=(460, 300), pos=(7, 7), value="", style=wx.TE_MULTILINE | wx.HSCROLL)

        self.RPC_check_box = wx.ComboBox(self.startWindow, value='Arb', pos=(7, 320), size=(63, 25), name='comboBox', choices=['Arb', 'Op', 'ETH', 'Matic'], style=16)
        self.RPC_check_box.Bind(wx.EVT_COMBOBOX, self.RPC_check_box_check)
        self.RPC_box = wx.TextCtrl(self.startWindow, size=(250, 25), pos=(70, 320), value='https://arb1.arbitrum.io/rpc', name='text', style=0)
        self.WETH_box = wx.RadioButton(self.startWindow, label='WETH', size=(70, 20), pos=(320, 320))
        self.WETH_box.SetValue(True)
        self.USDC_box = wx.RadioButton(self.startWindow, label='USDC', size=(70, 20), pos=(390, 320))

        self.Label6 = wx.StaticText(self.startWindow, size=(73, 20), pos=(7, 350), label='交易金额', name='staticText', style=2321)
        self.value_box = wx.TextCtrl(self.startWindow, size=(50, 20), pos=(80, 350), value='0.3', name='text', style=wx.TE_CENTER)

        self.Label9 = wx.StaticText(self.startWindow, size=(100, 20), pos=(130, 350), label='交易次数(对)', name='staticText', style=2321)
        self.times_box = wx.TextCtrl(self.startWindow, size=(50, 20), pos=(230, 350), value='15', name='text', style=wx.TE_CENTER)

        self.Label5 = wx.StaticText(self.startWindow, size=(30, 20), pos=(290, 350), label='gas', name='staticText', style=2321)
        self.GAS_box = wx.TextCtrl(self.startWindow, size=(50, 20), pos=(320, 350), value='0.1', name='text', style=wx.TE_CENTER)

        self.Label99 = wx.StaticText(self.startWindow, size=(40, 20), pos=(370, 350), label='延迟', name='staticText', style=2321)
        self.delay_box = wx.TextCtrl(self.startWindow, size=(40, 20), pos=(410, 350), value='5-10', name='text', style=wx.TE_CENTER)

        self.Label8 = wx.StaticText(self.startWindow, size=(50, 20), pos=(7, 380), label='私钥：', name='staticText', style=2321)
        self.private_key_box = wx.TextCtrl(self.startWindow, size=(250, 20), pos=(57, 380), value='', name='text', style=wx.TE_PASSWORD | wx.TE_CENTER)

        self.USDT_box = wx.RadioButton(self.startWindow, label='USDT', size=(70, 20), pos=(320, 380))
        self.start_button = wx.Button(self.startWindow, size=(40, 35), pos=(390, 375), label='开始', name='button')
        self.start_button.Bind(wx.EVT_BUTTON, self.start_button_click)
        pub.subscribe(self.multiText_updata, "update")
        self.RPC_check_box_check(1)
        pub.sendMessage("update", msg='欢迎使用odos刷交易  合作VX：Fooyao 推特：@fooyao158')
        pub.sendMessage("update", msg='选折WETH，即刷ETH-WETH交易对（马蹄为matic—Wmatic）')
        pub.sendMessage("update", msg='选USDC，即刷USDC-aUSDC交易对')
        pub.sendMessage("update", msg='将ETH转WETH再转回ETH,计一次交易')
        pub.sendMessage("update", msg='选择RPC节点，输入私钥，点击开始即可')
        pub.sendMessage("update", msg='-------------------------------------------------------------------')
        self.frame.Show(True)

    def multiText_updata(self, msg):
        self.multiText.AppendText(f'{time.strftime("[%H:%M:%S] ", time.localtime())}{msg}\n')

    def RPC_check_box_check(self, event):
        RPClist = ["https://arb1.arbitrum.io/rpc", "https://mainnet.optimism.io/",
                   "https://api.mycryptoapi.com/eth", "https://polygon-rpc.com"]
        RPC = RPClist[self.RPC_check_box.GetCurrentSelection()]
        self.RPC_box.SetValue(RPC)
        threading.Thread(target=self.get_gas, args=(self.RPC_box.GetValue(), 1), daemon=False).start()

    def get_gas(self, RPC, _):
        w3 = Web3(Web3.HTTPProvider(RPC))
        self.GAS_box.SetValue(str(w3.eth.gasPrice / 10 ** 9))

    def start_button_click(self, event):
        coin = self.USDT_box.GetValue() and 'USDT' or self.USDC_box.GetValue() and 'USDC' or 'WETH'
        sleep_time = [int(i) for i in self.delay_box.GetValue().split('-')]
        threading.Thread(target=token_swap, args=(self.RPC_box.GetValue(), self.value_box.GetValue(), self.times_box.GetValue(), self.GAS_box.GetValue(), self.private_key_box.GetValue(), coin, sleep_time), daemon=False).start()


def token_swap(RPC, value, times, gas_price, private_key, coin, sleep_time):
    coin_list = {'WETH': ['WETH'], 'USDC': ['USDC', 'aUSDC'], 'USDT': ['USDT', 'aUSDT']}
    task = TASK(RPC, value, gas_price, private_key, sleep_time)
    if task.state:
        try:
            if task.approve_token(*coin_list[coin]):
                wx.CallAfter(pub.sendMessage, "update", msg=f"-------------------------------------------------------------------")
                for i in range(int(times)):
                    if not task.swap_token(*coin_list[coin]):
                        time.sleep(1)
                        wx.CallAfter(pub.sendMessage, "update", msg='任务失败')
                        return
                    wx.CallAfter(pub.sendMessage, "update", msg=f'任务完成：{i + 1}/{times}')
                    wx.CallAfter(pub.sendMessage, "update", msg="-------------------------------------------------------------------")
                wx.CallAfter(pub.sendMessage, "update", msg=f'{times}次任务全部完成')
                wx.CallAfter(pub.sendMessage, "update", msg="-------------------------------------------------------------------")
        except Exception as e:
            wx.CallAfter(pub.sendMessage, "update", msg=f'任务失败：{e}')


class TASK:
    def __init__(self, RPC, value, gas_price, private_key, sleep_time):
        try:
            self.RPC = RPC
            self.w3 = Web3(Web3.HTTPProvider(self.RPC))
            self.vaule = self.w3.toWei(value, 'Mwei')
            self.chainid = self.w3.eth.chainId
            self.private_key = private_key
            self.gas_price = self.w3.toWei(gas_price, 'gwei')
            self.sleep_time = sleep_time

            self.allowance = {
                "inputs": [
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "address", "name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [
                    {"internalType": "uint256", "name": "", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
            self.approve = {
                'inputs': [
                    {'internalType': 'address', 'name': '_spender', 'type': 'address'},
                    {'internalType': 'uint256', 'name': '_tokens', 'type': 'uint256'}
                ],
                'name': 'approve',
                'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}],
                'stateMutability': 'nonpayable',
                'type': 'function'
            }
            self.balanceOf = {
                'inputs': [
                    {'internalType': 'address', 'name': '_user', 'type': 'address'}
                ],
                'name': 'balanceOf',
                'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
                'stateMutability': 'view',
                'type': 'function'
            }
            self.swap = {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "address", "name": "tokenAddress", "type": "address"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "address", "name": "receiver", "type": "address"},
                            {"internalType": "bytes", "name": "permit", "type": "bytes"}
                        ],
                        "internalType": "struct OdosRouter.inputToken[]",
                        "name": "inputs",
                        "type": "tuple[]"
                    },
                    {
                        "components": [
                            {"internalType": "address", "name": "tokenAddress", "type": "address"},
                            {"internalType": "uint256", "name": "relativeValue", "type": "uint256"},
                            {"internalType": "address", "name": "receiver", "type": "address"}
                        ],
                        "internalType": "struct OdosRouter.outputToken[]",
                        "name": "outputs",
                        "type": "tuple[]"
                    },
                    {"internalType": "uint256", "name": "valueOutQuote", "type": "uint256"},
                    {"internalType": "uint256", "name": "valueOutMin", "type": "uint256"},
                    {"internalType": "address", "name": "executor", "type": "address"},
                    {"internalType": "bytes", "name": "pathDefinition", "type": "bytes"}
                ],
                "name": "swap",
                "outputs": [
                    {"internalType": "uint256[]", "name": "amountsOut", "type": "uint256[]"},
                    {"internalType": "uint256", "name": "gasLeft", "type": "uint256"}
                ],
                "stateMutability": "payable",
                "type": "function"
            }
            self.swap_add = {
                42161: self.w3.toChecksumAddress("0xdd94018F54e565dbfc939F7C44a16e163FaAb331"),
                10: self.w3.toChecksumAddress("0x69dd38645f7457be13571a847ffd905f9acbaf6d"),
                1: self.w3.toChecksumAddress("0x76f4eeD9fE41262669D0250b2A97db79712aD855"),
                137: self.w3.toChecksumAddress("0xa32EE1C40594249eb3183c10792BcF573D4Da47C")
            }[self.chainid]
            self.swap_con = self.w3.eth.contract(address=self.swap_add, abi=[self.swap])
            self.zero_add = constants.ADDRESS_ZERO
            self.token_add = {
                'ETH': {
                    42161: self.zero_add,
                    10: self.zero_add,
                    1: self.zero_add,
                    137: self.zero_add

                },
                'WETH': {
                    42161: self.w3.toChecksumAddress("0x82af49447d8a07e3bd95bd0d56f35241523fbab1"),
                    10: self.w3.toChecksumAddress("0x4200000000000000000000000000000000000006"),
                    1: self.w3.toChecksumAddress("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
                    137: self.w3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
                },
                'USDC': {
                    42161: self.w3.toChecksumAddress("0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"),
                    10: self.w3.toChecksumAddress("0x7F5c764cBc14f9669B88837ca1490cCa17c31607"),
                    1: self.w3.toChecksumAddress("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
                    137: self.w3.toChecksumAddress("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
                },
                'aUSDC': {
                    42161: self.w3.toChecksumAddress("0x625E7708f30cA75bfd92586e17077590C60eb4cD"),
                    10: self.w3.toChecksumAddress("0x625E7708f30cA75bfd92586e17077590C60eb4cD"),
                    1: self.w3.toChecksumAddress("0xBcca60bB61934080951369a648Fb03DF4F96263C"),
                    137: self.w3.toChecksumAddress("0x1a13F4Ca1d028320A707D99520AbFefca3998b7F")
                },
                'USDT': {
                    42161: self.w3.toChecksumAddress("0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"),
                    10: self.w3.toChecksumAddress("0x94b008aA00579c1307B0EF2c499aD98a8ce58e58"),
                    1: self.w3.toChecksumAddress("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
                    137: self.w3.toChecksumAddress("0xc2132D05D31c914a87C6611C10748AEb04B58e8F")
                },
                'aUSDT': {
                    42161: self.w3.toChecksumAddress("0x6ab707aca953edaefbc4fd23ba73294241490620"),
                    10: self.w3.toChecksumAddress("0x6ab707Aca953eDAeFBc4fD23bA73294241490620"),
                    1: self.w3.toChecksumAddress("0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811"),
                    137: self.w3.toChecksumAddress("0x60D55F02A771d515e077c9C2403a1ef324885CeC")
                }
            }
            self.pool_add = {
                42161: self.w3.toChecksumAddress("0xdc723b71CA7eD367624a906a008893c69F291894"),
                10: self.w3.toChecksumAddress("0xd4A2269719276313aa6Ab7b01F91D238eBa96433"),
                1: self.w3.toChecksumAddress("0x1D64fB0fFa8362B2E1Ee7ee03929159551Eab26e"),
                137: self.w3.toChecksumAddress("0x10fC1fa5D02EB99D2274A5F5E7dD448F2b03e402")
            }[self.chainid]
            self.token_con = self.w3.eth.contract(address=self.zero_add, abi=[self.approve, self.balanceOf, self.allowance])
            if self.gas_price == 0:
                self.gas_price = int(self.w3.eth.gasPrice * 1.1)
            self.account = self.w3.eth.account.privateKeyToAccount(self.private_key)
            self.nonce = self.w3.eth.getTransactionCount(self.account.address)
            self.state = True
        except Exception as e:
            wx.CallAfter(pub.sendMessage, "update", msg=f'初始化失败: {e}')
            self.state = False

    def approve_token(self, token_name, token_name2=None):
        try:
            approve_token_add = self.token_add[token_name][self.chainid]
            value = (self.vaule, int(self.vaule * 10 ** 12))[token_name == 'WETH']
            token_allowance = self.token_con.functions.allowance(self.account.address, self.swap_add).call({'to': approve_token_add})
            if token_allowance > value * 100:
                wx.CallAfter(pub.sendMessage, "update", msg=f"{token_name}授权额度足够，无需再次授权")
                return token_name2 is None and True or self.approve_token(token_name2)
            else:
                tx = self.token_con.functions.approve(self.swap_add, int(10 ** 27)).buildTransaction({
                    'from': self.account.address,
                    'chainId': self.chainid,
                    'gas': 1000000,
                    'gasPrice': self.gas_price,
                    'nonce': self.nonce
                })
                tx['to'] = approve_token_add
                estimateGas = self.w3.eth.estimateGas(tx)
                tx['gas'] = int(estimateGas * 1.3)
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
                try:
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    wx.CallAfter(pub.sendMessage, "update", msg=f"授权{token_name}发送成功")
                    wx.CallAfter(pub.sendMessage, "update", msg=self.w3.toHex(tx_hash))
                    freceipt = self.w3.eth.waitForTransactionReceipt(tx_hash, 3000)
                    if freceipt.status == 1:
                        wx.CallAfter(pub.sendMessage, "update", msg=f"授权{token_name}成 功")
                        self.nonce += 1
                        random_sleep = random.randint(*self.sleep_time)
                        wx.CallAfter(pub.sendMessage, "update", msg=f"随机延迟{random_sleep}秒")
                        time.sleep(random_sleep)
                        return token_name2 is None and True or self.approve_token(token_name2)
                    else:
                        wx.CallAfter(pub.sendMessage, "update", msg=f"授权{token_name}交易失败")
                        return False
                except Exception as e:
                    wx.CallAfter(pub.sendMessage, "update", msg=f'{token_name}授权失败: {e}')
                    return False
        except Exception as e:
            wx.CallAfter(pub.sendMessage, "update", msg=f'{token_name}授权失败: {e}')
            return False

    def swap_token(self, from_token_name, to_token_name=None):
        try:
            if to_token_name is None:
                from_token_name = 'ETH'
                to_token_name = 'WETH'
            from_token_add = self.token_add[from_token_name][self.chainid]
            to_token_add = self.token_add[to_token_name][self.chainid]
            value = (self.vaule, int(self.vaule * 10 ** 12))['ETH' in from_token_name]
            ETH_value = 0
            token_balance = from_token_name == 'ETH' and 1 or self.token_con.functions.balanceOf(self.account.address).call({'to': from_token_add})
            unkonwid = (6, 7)[self.chainid == 137]
            if from_token_name == 'ETH':
                ETH_value = value
                permit = f'0x01020200050101020201ff{to_token_add[2:].lower().zfill(82)}'
                eth_balance = self.w3.eth.getBalance(self.account.address)
                if eth_balance <= self.vaule:
                    wx.CallAfter(pub.sendMessage, "update", msg='ETH余额不足')
                    return False
            elif from_token_name == 'WETH':
                permit = '0x010201000501000201ff00000000000000000000000000000000000000000000'
                value = token_balance
            elif 'a' in from_token_name:
                permit = f'0x010203000{unkonwid}0101010200ff{from_token_add[2:].lower().zfill(82)}{to_token_add[2:].lower()}'
                value = token_balance
            else:
                permit = f'0x010203000{unkonwid}0101010201ff{from_token_add[2:].lower().zfill(82)}{to_token_add[2:].lower()}'
                value = (token_balance, value)[token_balance >= value]
            tx = self.swap_con.functions.swap(
                [(from_token_add, value, self.pool_add, b"")],
                [(to_token_add, 1, self.account.address)],
                value, int(value * 0.99), self.pool_add, permit
            ).buildTransaction({
                'from': self.account.address,
                'chainId': self.chainid,
                'gas': 2000000,
                'gasPrice': self.gas_price,
                'nonce': self.nonce,
                'value': ETH_value
            })
            estimateGas = self.w3.eth.estimateGas(tx)
            tx['gas'] = int(estimateGas * 1.3)
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            try:
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                wx.CallAfter(pub.sendMessage, "update", msg=f"兑换{from_token_name}到{to_token_name}交易发送成功")
                wx.CallAfter(pub.sendMessage, "update", msg=self.w3.toHex(tx_hash))
                freceipt = self.w3.eth.waitForTransactionReceipt(tx_hash, 3000)
                if freceipt.status == 1:
                    input_value, get_value = 0, 0
                    if to_token_name == 'ETH':
                        get_value = self.w3.eth.getBalance(freceipt['from'], freceipt.blockNumber) - self.w3.eth.getBalance(freceipt['from'], freceipt.blockNumber - 1) + freceipt.gasUsed * freceipt.effectiveGasPrice
                        get_value = self.w3.fromWei(get_value, 'ether')
                        input_value = self.w3.fromWei(value, 'ether')
                    else:
                        for x in freceipt.logs:
                            if x.topics[0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                                to_add = self.w3.toChecksumAddress(f'0x{x.topics[2].hex()[-40:]}')
                                from_add = self.w3.toChecksumAddress(f'0x{x.topics[1].hex()[-40:]}')
                                if from_add == freceipt['from']:
                                    input_value = self.w3.toInt(hexstr=x['data'])
                                elif to_add == freceipt['from']:
                                    get_value = self.w3.toInt(hexstr=x['data'])
                        get_value = (self.w3.fromWei(get_value, 'Mwei'), self.w3.fromWei(get_value, 'ether'))['WETH' == to_token_name]
                        input_value = (self.w3.fromWei(input_value, 'Mwei'), self.w3.fromWei(value, 'ether'))['WETH' == to_token_name]
                    wx.CallAfter(pub.sendMessage, "update", msg=f"兑换{input_value}【{from_token_name}】到{get_value}【{to_token_name}】交易成功")
                    self.nonce += 1
                    random_sleep = random.randint(*self.sleep_time)
                    wx.CallAfter(pub.sendMessage, "update", msg="-------------------------------------------------------------------")
                    wx.CallAfter(pub.sendMessage, "update", msg=f"随机延迟{random_sleep}秒")
                    time.sleep(random_sleep)
                    return len(from_token_name) > len(to_token_name) and True or self.swap_token(to_token_name, from_token_name)
                else:
                    wx.CallAfter(pub.sendMessage, "update", msg=f"兑换{from_token_name}到{to_token_name}交易失败")
                    return False
            except Exception as e:
                wx.CallAfter(pub.sendMessage, "update", msg=f'兑换{from_token_name}到{to_token_name}交易失败: {e}')
                return False
        except Exception as e:
            wx.CallAfter(pub.sendMessage, "update", msg=f'兑换{from_token_name}到{to_token_name}交易失败: {e}')
            return False


def killpid(selfpid, _):
    os.kill(selfpid, signal.SIGINT)


if __name__ == '__main__':
    app = Myapp()
    app.MainLoop()
    spid = os.getpid()
    threading.Thread(target=killpid, args=(spid, 0), daemon=False).start()
