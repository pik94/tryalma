from tronpy.keys import PrivateKey


def get_random_trx_address() -> str:
    key = PrivateKey.random()
    pubkey = key.public_key
    return pubkey.to_base58check_address()
