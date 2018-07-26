import bitcoin_secp256k1
from bitcoin_secp256k1 import P
import binascii
import bitcoin_base58
import base58
import hash_utils
import bitcoin_bech32

network_type = ['mainnet', 'testnet', 'regtest']_
segwit_address_prefix = {'mainnet': 'bc', 'testnet': 'tb', 'regtest': 'bcrt'}

def compressPubkey(pubkey: bytes):
        x_b = pubkey[1:33]
        y_b = pubkey[33:65]
        if (y_b[31] & 0x01) == 0: # even
                compressed_pubkey = b'\02' + x_b
        else:
                compressed_pubkey = b'\03' + x_b
        return compressed_pubkey

def privkey2pubkey(privkey: int, compress: bool):
        bitcoin_sec256k1 = bitcoin_secp256k1.BitcoinSec256k1()
        pubkey = bitcoin_sec256k1.privkey2pubkey(privkey)
        full_pubkey = b'\x04' + binascii.unhexlify(str('%064x' % pubkey[0])) + binascii.unhexlify(str('%064x' % pubkey[1]))
        if compress == True:
                compressed_pubkey = compressPubkey(full_pubkey)
                return compressed_pubkey
        return full_pubkey

def uncompressPubkey(x_b: bytes):
        prefix = x_b[0:1]
        print('prefix = %s' % prefix)
        print('(p+1)/4 = %d' % ((P + 1) >> 2))
        x_b = x_b[1:33]
        x = int.from_bytes(x_b, byteorder='big')

        y_square = (pow(x, 3, P)  + 7) % P
        y_square_square_root = pow(y_square, ((P+1) >> 2), P)
        if (prefix == b"\x02" and y_square_square_root & 1) or (prefix == b"\x03" and not y_square_square_root & 1):
            y = (-y_square_square_root) % P
        else:
            y = y_square_square_root

        y_b = y.to_bytes(32, 'big')
        full_pubkey_b = b''.join([b'\x04', x_b, y_b])
        return full_pubkey_b

### pre-segwit [
def pkh2address(pkh: bytes, is_testnet: bool):
        address = bitcoin_base58.forAddress(pkh, is_testnet, False)
        return address

def pubkey2address(pubkey: bytes, is_testnet: bool):
        pkh = hash_utils.hash160(pubkey)
        print('pkh = %s' % bytes.decode(binascii.hexlify(pkh)))
        address = pkh2address(pkh, is_testnet)
        return address

def sh2address(sh: bytes, is_testnet: bool):
        address = bitcoin_base58.forAddress(sh, is_testnet, True)
        return address

def redeemScript2address(script: bytes, is_testnet: bool):
        sh = hash_utils.hash160(script)
        address = sh2address(sh, is_testnet)
        return address

### ] segwit [
def hash2segwitaddr(witprog: bytes, nettype: str):
        witver = 0x00
        hrp = segwit_address_prefix[nettype]
        address = witnessProgram2address(hrp, witver, witprog)
        return address

def pubkey2segwitaddr(pubkey: bytes, nettype: str):
        pkh = hash_utils.hash160(pubkey)
        print('pkh = %s' % bytes.decode(binascii.hexlify(pkh)))
        address = hash2segwitaddr(pkh, nettype)
        return address
### ]

def pubkey2address(pubkey: bytes, nettype: str, is_segwit: bool):
        pkh = hash_utils.hash160(pubkey)
        print('pkh = %s' % bytes.decode(binascii.hexlify(pkh)))
        address = hash2address(pkh, nettype, is_segwit, is_script=False)
        return address

def hash2address(h: bytes, nettype: str, is_segwit: bool, is_script: bool):
        if is_script:
                if is_segwit:
                        address = hash2segwitaddr(h, nettype)
                else:
                        address = sh2address(h, nettype == 'testnet')
        else:
                if is_segwit:
                        address = hash2segwitaddr(h, nettype)
                else:
                        address = pkh2address(h, nettype == 'testnet')

def addressCheckVerify(address: str):
        is_valid = False
        if address[0] in ['1', '3', 'm', 'n', '2']:
                is_valid = bitcoin_base58.addressVerify(address)
        elif address[0:3] in [
                                'bc1', # mainnet
                                'tb1', # testnet
                                'bcrt1' # regtest
                             ]:
                is_valid = bitcoin_bech32.addressVerify(address)
        return is_valid

def witnessProgram2address(hrp: str, witver: int, witprog: bytes):
        return bitcoin_bech32.encode(hrp, witver, witprog)

def privkeyHex2Wif(privkey: int, is_testnet: bool, for_compressed_pubkey: bool):
        wif = bitcoin_base58.encodeWifPrivkey(privkey, is_testnet, for_compressed_pubkey)
        return wif

def privkeyWif2Hex(privkey: str):
        privkey, for_compressed_pubkey = bitcoin_base58.decodeWifPrivkey(privkey)
        return privkey, for_compressed_pubkey

if __name__ == '__main__':
        pubkey = privkey2pubkey(0x18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725, False)
        print ('Full pubkey = %s' % bytes.decode(binascii.hexlify(pubkey)))
        pubkey = privkey2pubkey(0x18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725, True)
        print ('compressed pubkey = %s' % bytes.decode(binascii.hexlify(pubkey)))
        address = pubkey2address(pubkey, False)
        print('address = %s' % address)
        pubkey = uncompressPubkey(pubkey)
        print ('uncompressed pubkey = %s' % bytes.decode(binascii.hexlify(pubkey)))
        is_valid = addressCheckVerify(address)
        print('Is Address valid: %r' % is_valid)
        h160 = 'e9c3dd0c07aac76179ebc76a6c78d4d67c6c160a'
        address = sh2address(binascii.unhexlify(h160), False)
        print ('P2SH address = %s' % address)
        is_valid = addressCheckVerify(address)
        print('Is Address valid: %r' % is_valid)
        witprog = binascii.unhexlify('701a8d401c84fb13e6baf169d59684e17abd9fa216c8cc5b9fc63d622ff8c58d')
        witver = 0x00
        hrp = 'bc'
        address = witnessProgram2address(hrp, witver, witprog)
        print('WSH witness address = %s' % address)
        # block hash 0000000000000000000e377cd4083945678ad30c533a8729198bf3b12a8e9315 and tx index 68
        # txn id: ae06fd062b65b7c99dfd3787cb6fa3d46a9c7371e3ca303e0be87fc0e245d775
        witprog_str = '0178ec3c35f8d096f062585deb285d22ab645d83'
        witprog = binascii.unhexlify(witprog_str)
        witver = 0x00
        hrp = 'bc'
        address = witnessProgram2address(hrp, witver, witprog)
        print('Mainnet WPKH witness address = %s for witness program = %s' % (address, witprog_str))
        witver = 0x00
        hrp = 'tb'
        address = witnessProgram2address(hrp, witver, witprog)
        print('Testnet WPKH witness address = %s for witness program = %s' % (address, witprog_str))
        witver = 0x00
        hrp = 'bcrt'
        address = witnessProgram2address(hrp, witver, witprog)
        print('Regtest WPKH witness address = %s for witness program = %s' % (address, witprog_str))
        privkey_wif = privkeyHex2Wif(0xef235aacf90d9f4aadd8c92e4b2562e1d9eb97f0df9ba3b508258739cb013db2, False, True)
        print('private key in WIF format = %s' % privkey_wif)
        address = pubkey2address(binascii.unhexlify('02340886131f76166c8b4fec75b59b23a49a45ea0ffc016eeecd404ae58e0196c0'), True)
        print('testnet address = %s' % address)