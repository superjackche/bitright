#!/usr/bin/env python
import os
import hashlib
import mimetypes
from flask import Flask, request, render_template, jsonify, redirect, send_from_directory, make_response
from blockchain import Blockchain, Block
import json

from settings import CONFIG, UPLOAD_FOLDER, TMP_FOLDER, CHAIN_FILE
from acoustid import FingerprintGenerationError

app =  Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TMP_FOLDER'] = TMP_FOLDER

# the node's copy of blockchain

blockchain = Blockchain()

if os.path.exists(CHAIN_FILE):
	with open(CHAIN_FILE, encoding='utf-8') as source:
		blockchain.chain = [Block.from_dict(row) for row in json.load(source)]

for directory in (os.path.dirname(CHAIN_FILE), UPLOAD_FOLDER, TMP_FOLDER):
    if not os.path.exists(directory):
        os.makedirs(directory)
if not blockchain.check_integrity():
    raise ValueError("Stored blockchain failed integrity verification")

@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/blockchain')
def blockchain_page():
    return render_template('./blockchain.html')

@app.route('/about')
def about_page():
    return render_template('./aboutus.html')

@app.route('/faq')
def faq_page():
    return render_template('./faq.html')

@app.route('/uploads/<path:filename>')
def custom_static(filename):
    media = filename.split('.')[0]
    original = next((b.transaction['filename'] for b in blockchain.chain
                     if b.transaction['media'] == media), '')
    response = make_response(send_from_directory(UPLOAD_FOLDER, media))
    response.headers['Content-Type'] = mimetypes.guess_type(original)[0] or 'application/octet-stream'
    return response


# @app.route('/new_transaction', methods=['POST'])
# def new_transaction():
# 	sender = request.form["sender"]
# 	recipient = request.form["recipient"]
# 	value = request.form["value"]

# 	blockchain.new_transaction(sender, recipient, value)

# 	return redirect('/')

# @app.route('/pending_tx')
# def get_pending_tx():
# 	transactions = blockchain.unconfirmed_transactions
# 	response = {'transactions': transactions}
# 	return jsonify(response), 200

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
	result = blockchain.mine()
	if result is None:
		return jsonify({'ok': False, 'message': 'No valid pending transaction'}), 400
	response = {'block': result.__dict__}

	return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def get_chain():
	chain_data = []
	for block in blockchain.chain:
		chain_data.append(block.__dict__)

	response = {'chain': chain_data}
	return jsonify(response), 200

# @app.route('/get_block', methods=['POST'])
# def get_block():
# 	index = int(request.form["block_index"])
# 	block = blockchain.chain[index]

# 	response = {'block': block.__dict__}

# 	return jsonify(response), 200

# @app.route('/reset')
# def reset():
# 	global blockchain

# 	blockchain = Blockchain()

# 	return redirect('/')

@app.route('/integrity', methods=['GET'])
def integrity():
    return jsonify({'integrity': blockchain.check_integrity()}), 200


@app.route('/upload', methods=['POST'])
def upload():
	global blockchain

	print(request)
	if 'contentFile' not in request.files:
		response = {'ok': False}
		return jsonify(response), 500
	file = request.files['contentFile']

	filename = hashlib.sha256(file.read()).hexdigest()
	file.seek(0) #reset read pointer

	action = request.form['action']
	if action not in ('lookup', 'publish') or request.form['genre'] not in ('Text', 'Image', 'Audio'):
		return jsonify({'ok': False, 'message': 'Invalid action or media type'}), 400

	try:
		if action == "lookup":
			#TODO search for exact and partial matches
			print('TODO lookup')
			file.save(os.path.join(app.config['TMP_FOLDER'], filename))
			lookup_media = {
	            'genre': request.form['genre'],
	            'media': filename,
	        }
			result = blockchain.lookup(lookup_media)
			os.remove(os.path.join(app.config['TMP_FOLDER'], filename)) #remove uploaded file

			if result is None:
				response = {'unique': True}
				return jsonify(response), 200

			response = {'unique': False, 'block': result.__dict__, 'message': 'Similar Object Detected'}

			return jsonify(response), 200
		elif action == "publish":
			if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
				print("Duplicate Detected")
				response = {'unique': False, 'message':'Duplicate Detected'}
			else:
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				#Create a new transaction
				author = request.form['author']
				title = request.form['title']
				pubkey = request.form['pubkey']
				genre = request.form['genre']
				original_filename = file.filename
				blockchain.new_transaction(title, original_filename, author, pubkey, genre, filename)
				result = blockchain.mine()
				if result == None:
					print("FALSE")
					os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #remove uploaded file
					response = {'unique': False, 'message':'Similar Object Detected, Input File Rejected'}
				else:
					print("TEST")
					print(result)
					response = {'unique': True, 'block': result.__dict__}

			return jsonify(response), 200
	except (IOError, OSError, ValueError, FingerprintGenerationError):
		app.logger.exception("Media processing failed")
		blockchain.unconfirmed_transactions = {}
		if action == 'lookup' or not any(b.transaction['media'] == filename for b in blockchain.chain):
			path = os.path.join(TMP_FOLDER if action == 'lookup' else UPLOAD_FOLDER, filename)
			if os.path.exists(path):
				os.remove(path)
		return jsonify({'ok': False, 'message': 'Media processing failed; check server log'}), 422


if __name__ == '__main__':
    app.run(host=CONFIG['host'], port=CONFIG['port'], debug=CONFIG['debug'], threaded=False)
