from time import time
import datetime
import os
import hashlib as hasher
import json
from settings import UPLOAD_FOLDER, TMP_FOLDER, CHAIN_FILE
import acoustic.acoustid_check as ac
import text_compare.test_text as tc
import image_compare.image_check as ic

""" Class for transactions made on the blockchain. Each transaction has a
    sender, recipient, and value.
    """
class Transaction: 
    
    """ Transaction initializer """
    def __init__(self, title="", filename="", author="", public_key="", genre="", media = ""):
        self.title = title
        self.filename = filename
        self.author = author
        self.public_key = public_key
        self.genre = genre
        self.media = media

    
    """ Converts the transaction to a dictionary """
    def toDict(self):
        return {
            'title': self.title,
            'filename': self.filename,
            'author': self.author,
            'public_key': self.public_key,
            'genre': self.genre,
            'media': self.media,
    }

    def __str__(self):
        toString = self.author + " : " + self.genre + " (" + self.media + ") "
        return toString;

""" Class for Blocks. A block is an object that contains transaction information
    on the blockchain.
    """
class Block:
    def __init__(self, index, transaction, previous_hash):
        
        self.index = index
        self.timestamp = time()
        self.previous_hash = previous_hash
        self.transaction = transaction
        self.hash = self.compute_hash()
    
    @classmethod
    def from_dict(cls, data):
        block = cls(data['index'], data['transaction'], data['previous_hash'])
        block.timestamp = data['timestamp']
        block.hash = data['hash']
        return block

    def compute_hash(self):
        concat_str = json.dumps(self.serialize(), sort_keys=True, separators=(',', ':'))
        hash_result = hasher.sha256(concat_str.encode('utf-8')).hexdigest()
        return hash_result

    def serialize(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'transaction': self.transaction
        }


""" Blockchain class. The blockchain is the network of blocks containing all the
    transaction data of the system.
    """
class Blockchain:
    def __init__(self):
        
        
        self.unconfirmed_transactions = {}
        self.chain = []
    
    def create_genesis_block(self):
        empty_media = {
            'title': "",
            'filename': "",
            'author': "",
            'public_key': "",
            'genre': "",
            'media': "",
        }
        new_block = Block(index=0, transaction=empty_media, previous_hash=0)
        self.add_block(new_block)

        return new_block
    
    def new_transaction(self, title, filename, author, public_key, genre, media):
        new_trans = Transaction(title, filename, author, public_key, genre, media).toDict();
        self.unconfirmed_transactions= new_trans.copy()
        return new_trans
    
    def mine(self):
        if not self.unconfirmed_transactions:
            return None
        if not self.check_integrity():
            raise ValueError("Blockchain integrity check failed")
        #create a block, verify its originality and add to the blockchain
        if (len(self.chain) ==0):
            block_idx = 1
            previous_hash = 0
        else:
            block_idx = self.chain[-1].index + 1
            previous_hash = self.chain[-1].compute_hash()
        block = Block(block_idx, self.unconfirmed_transactions, previous_hash)
        self.unconfirmed_transactions = {}
        if(self.verify_block(block)):
            self.add_block(block)
            return block
        else:
            return None
    
    def verify_block(self, block):
        #verify song originality and previous hash
        #check previous hash

        if len(self.chain) ==0:
            previous_hash = 0
        else:
            previous_hash = self.chain[-1].compute_hash()
        if block.previous_hash != previous_hash:
            return 0
        #check originality
        for prev_block in self.chain:
           if block.transaction['genre'] == prev_block.transaction['genre']:
                if block.transaction['genre'] == 'Audio':
                    score = ac.calc_accuracy(UPLOAD_FOLDER + os.sep + block.transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score > 0.9:
                      return 0
                if block.transaction['genre'] == 'Text':
                    score = tc.check_text_similarity(UPLOAD_FOLDER + os.sep + block.transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score < 100:
                        return 0
                if block.transaction['genre'] == "Image":
                    score = ic.calc_accuracy(UPLOAD_FOLDER + os.sep + block.transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score < 0.4:
                        return 0
        return 1

    def lookup(self, transaction):
        #check originality
        for prev_block in self.chain:
           if transaction['genre'] == prev_block.transaction['genre']:
                if transaction['genre'] == 'Audio':
                    score = ac.calc_accuracy(TMP_FOLDER + os.sep + transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score > 0.9:
                      return prev_block
                if transaction['genre'] == 'Text':
                    score = tc.check_text_similarity(TMP_FOLDER + os.sep + transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score < 100:
                        return prev_block
                if transaction['genre'] == "Image":
                    score = ic.calc_accuracy(TMP_FOLDER + os.sep + transaction['media'], UPLOAD_FOLDER + os.sep + prev_block.transaction['media'])
                    print(score)
                    if score < 0.4:
                        return prev_block
        return None
    
    def add_block(self, block):
        self.chain.append(block)

        with open(CHAIN_FILE + '.tmp', 'w', encoding='utf-8') as output:
            json.dump([block.__dict__ for block in self.chain], output, ensure_ascii=False, indent=2)
        os.replace(CHAIN_FILE + '.tmp', CHAIN_FILE)

    
    def check_integrity(self):
        previous_hash = 0
        for index, block in enumerate(self.chain, 1):
            if (block.index != index or block.previous_hash != previous_hash
                    or block.hash != block.compute_hash()):
                return False
            with open(os.path.join(UPLOAD_FOLDER, block.transaction['media']), 'rb') as media:
                if hasher.sha256(media.read()).hexdigest() != block.transaction['media']:
                    return False
            previous_hash = block.hash
        return True

    """ Function that returns the last block on the chain"""
    @property
    def last_block(self):
        return self.chain[-1]
