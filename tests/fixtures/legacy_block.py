# Original Block from liuyanqi/bitright b8d0b694, retained for comparison.
from time import time
import hashlib as hasher

class Block:
    def __init__(self, index, transaction, previous_hash):

        self.index = index
        self.timestamp = time()
        self.previous_hash = previous_hash
        self.transaction = transaction

    def compute_hash(self):
        concat_str = str(self.index) + str(self.timestamp) + str(self.previous_hash) + str(self.transaction['author']) + str(self.transaction['genre'])
        hash_result = hasher.sha256(concat_str.encode('utf-8')).hexdigest()
        return hash_result

    def serialize(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'transaction': self.transaction
        }
