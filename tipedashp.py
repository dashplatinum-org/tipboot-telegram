#-*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
from datetime import datetime, time
import requests
import logging
import pymongo
import json
import sys
import subprocess
#reload(sys)
#sys.setdefaultencoding('utf8')

config = json.loads(open("dashp.json").read())

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)

def ajuda(bot, update):
        update.message.reply_text("Commandos Disponiveis:\n/info - Informaçao Do Projeto\n/regras <regras do grupo>\n/reiniciar <iniciar novos registros>\n/valor preço do dashp\n/converter <quantidade> <moeda> <moeda>\n/registrar - <@nickname>\n/depositar - mostra <carteira>\n/enviar <user> <valor>\n/distribuir <valor>\n/saldo - ver saldo\n/sacar - <carteira> <valor>")

def info(bot, update):
        update.message.reply_text("Especificaçoes da Moeda\nTotal Coin Supply (premine) 2% | 394,000 DASHP\nMax Coin Supply (PoW/POS/MN) | 19,700,000 DASHP\nBlock Time | 180 Seconds\nMaturidade 3 horas\nReward 80% Masternode | 20% Stake\nReconpenças Por Bloco\n0004 to 14399 = 1.10 DASHP\n14400 to 28799 = 1.70 DASHP\n28800 to 43199 = 2.60 DASHP\n43200 to 57599 = 2.90 DASHP\n57600 to 172799 = 5.10 DASHP\n345600 to 518399 = 4.05 DASHP\n518400 to 604799 = 3.64 DASHP\n604800 to 5149846 = 3.28 DASHP\n5149846 forward = 3.28 DASHP\ngithub https://github.com/dashplatinum-org/dashplatinum\nwallets https://github.com/dashplatinum-org/dashplatinum/releases\nwebsite https://dashplatinum.org\nexplorer https://explorer.dashplatinum.org\nExchange Listing\nCREX24: https://crex24.com/pt/exchange/DASHP-BTC\nStake Pool and Shared Masternode\nhttps://simplepospool.com/?ref=Feliciosxavier\nShared Masternode\nhttps://node.trittium.cc\nhttps://www.cryptohashtank.com/masternodes/DASHP\nMasternodes System\nhttps://central.zcore.cash/mn/DASHP\nPlatform of Masternde Klimatas:\nhttps://hub.klimatas.com/available-coins\nPlatform of Masternde Gentarium:\nhttps://mn.gtmcoin.io\nFlitsNode Mobile Masternode Service:\nhttps://flitsnode.app\nIhostMn:\nhttps://ihostmn.com/hostmn.php?coin=DASHP\n") 

def get_mongo():
	client = pymongo.MongoClient("127.0.0.1:27017")
	return client["DASHP"]


def get_user_id(user):
	db = get_mongo()

	u = db.users.find_one({'username': user})

	return u


def get_user(user):
	db = get_mongo()

	u = db.users.find_one({'userid': user})

	if u is None:
		u = {'userid': user}
		db.users.insert(u)

	return u


def add_to_chat(user, chat):
	db = get_mongo()

	db.users.update({'userid': user['userid']}, {'$addToSet': {'chats': chat}})


def is_registered(user):
	db = get_mongo()

	return db.users.count({'username': user}) != 0


def is_registered_id(user):
	db = get_mongo()

	return db.users.count({'userid': user}) != 0


def give_balance(user, amount):
	db = get_mongo()

	db.users.update({'userid': user['userid']},
					{'$inc': {'redeemed': float(-amount)}})

	return db.users.find_one({'userid': user['userid']})


def get_balance(user):
	db = get_mongo()

	rpc = AuthServiceProxy("http://%s:%s@%s:%d" %
						(config['rpc']['user'], config['rpc']['password'],
							config['rpc']['host'], config['rpc']['port']))

	address = get_address(user)

	received = rpc.getreceivedbyaddress(address)

	return received - Decimal(db.users.find_one(
								{'userid': user['userid']}).get('redeemed', 0))


def get_unconfirmed(user):
	rpc = AuthServiceProxy("http://%s:%s@%s:%d" %
						(config['rpc']['user'], config['rpc']['password'],
							config['rpc']['host'], config['rpc']['port']))
	address = get_address(user)

	received = rpc.getreceivedbyaddress(address)
	received_unconfirmed = rpc.getreceivedbyaddress(address, 0)

	return received_unconfirmed - received


def validate_address(address):
	rpc = AuthServiceProxy("http://%s:%s@%s:%d" %
						(config['rpc']['user'], config['rpc']['password'],
							config['rpc']['host'], config['rpc']['port']))
	return rpc.validateaddress(address)['isvalid']


def get_address(user):
	db = get_mongo()

	address = db.users.find_one({'userid': user['userid']}) \
				.get('address', None)

	if address is None:
		rpc = AuthServiceProxy("http://%s:%s@%s:%d" %
							   (config['rpc']['user'],
								config['rpc']['password'],
								config['rpc']['host'], config['rpc']['port']))
		address = rpc.getnewaddress()
		db.users.update({'userid': user['userid']},
						{'$set': {'address': address}})

	return address


def regras(bot, update):
	 update.message.reply_text('Os dono do boot @Dashp_official  poderar resetar os registros a qualquer momento\nFique atento sempre fique online e digite /registrar sempre que possivel\nPara pedir seu proprio bot entre em contato com @FelicioXavier')

def start(bot, update):
	update.message.reply_text('Olá eu sou um wallet e tipbot oficil do grupo @Dashp_official\nRegistre-se para participar e ganhar DASHP. \nLembre-se nao sou carteira para guardar moedas\nevite armazenar altos valores em mim. \nA taxa para saque é 1 dashp. Use\n/registrar  para registrar ou use\n/ajuda para ver todos commandos\nPeça  seu bot personalizado de qualquer moeda envi uma mensagem para @FelicioXavier')

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)
	
def enviar(bot, update):
	args = update.message.text.split()[1:]

	if len(args) == 2:
		# Unfortunatelly the only way i can currently think of for getting the
		# user ID for the username is if I get the user to register first.
		# Sucks, but I guess I need it to be done
		user = get_user_id(args[0])
		from_user = get_user(update.message.from_user.id)
		try:
			amount = Decimal(args[1])
		except decimal.InvalidOperation:
			update.message.reply_text("Uso: /enviar <user> <valor>")
			return

		if user is not None:
			if amount > .1:
				if get_balance(from_user) - amount >= .1:
					from_user = give_balance(from_user, -amount)
					user = give_balance(user, amount)
					bot.sendMessage(chat_id=update.message.chat_id,
									text="Visite @Dashp_official e conheça a criptomoeda brasileira! %s enviou %s %f DASHP" % (
										from_user['username'],
										args[0],
										amount
									))
				else:
					update.message.reply_text("Saldo Insuficiente! Seu Saldo Restante deve ser maior que 0.1")
			else:
				update.message.reply_text("Valor Invalido! Valor Minimo Deve ser Maior que 0.1")
		else:
			update.message.reply_text("%s nao esta registrado!" % (args[0]))
	else:
		update.message.reply_text("Uso: /enviar <user> <valor>")

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)


def distribuir(bot, update):
	args = update.message.text.split()[1:]
	if len(args) == 1:
		from_user = get_user(update.message.from_user.id)
		try:
			amount = Decimal(args[0])
		except decimal.InvalidOperation:
			update.message.reply_text("Uso: /distribuir <valor>")
			update.message.reply_text("Valor Minimo Deve ser Maior que 0.1")
			return

		if amount > .1:
			if get_balance(from_user) - amount >= .1:
				db = get_mongo()

				users = db.users.find({'chats': update.message.chat_id,
									   'userid': {'$ne': from_user['userid']},
									   'username': {'$ne': None}})

				if users.count() > 0:
					tip = amount/users.count()
					from_user = give_balance(from_user, -amount)

					usernames = []

					for user in users:
						#print(user)
						give_balance(user, tip)
						usernames.append(user['username'])

					users_str = ", ".join(usernames)

					print(users.count())

					for user in users:
						#print(user)
						give_balance(user, tip)

					bot.sendMessage(chat_id=update.message.chat_id,
									text="Visite @Dashp_official e conheça a criptomoeda brasileira!! %s enviou %f DASHP para %s!" % (
										from_user['username'],
										tip,
										users_str
									))
				else:
					update.message.reply_text("Nao Existe Usuarios Registrado Nesse Canal"
											  " ou Grupo.")
			else:
				update.message.reply_text("Saldo Insuficiente! Saldo minimo Deve ser maior que 0.1")
		else:
			update.message.reply_text("Valor Invalido, valor minimo deve ser maior que 0.1")
	else:
		update.message.reply_text("Uso: /distribuir <valor>")

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)


def saldo(bot, update):
	user = update.message.from_user.username
	if user is "":
		update.message.reply_text("Por Favor Insira um nickname na configuraçao do telegram!")
		return
	else:
		bal = get_balance(get_user(update.message.from_user.id))

#	r = requests.get('https://api.cryptonator.com/api/ticker/%s-%s' %
#					 ('ok', 'usd'))
#	usd = Decimal(bal)*Decimal(r.json()['ticker']['price'])

		unconfirmed = ""

		if get_unconfirmed(get_user(update.message.from_user.id)) > 0:
			unconfirmed = "(%1.8f unconfirmed)" % \
						  get_unconfirmed(get_user(update.message.from_user.id))

		update.message.reply_text("Seu Saldo é: %1.8f DASHP" % + bal, unconfirmed)

		add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)


def registrar(bot, update):
        user = update.message.from_user.username
        if user is "":
                update.message.reply_text("Por Favor Insira um nickname na configuraçao do telegram!")
                return
        else:

                username = "@" + update.message.from_user.username

                if not is_registered_id(update.message.from_user.id):
                        if not is_registered(username):
                                db = get_mongo()

                                db.users.insert_one({'username': username,
                                                                         'userid': update.message.from_user.id})
                                update.message.reply_text("Você  foi Registrado como %s" %
                                                                                  username)

                else:
                        db = get_mongo()

                        db.users.update({'userid': update.message.from_user.id},
                                                        {'$set': {'username': username}})
                        update.message.reply_text("Seu Registro foi Atualizado Para %s" % username)
			
        add_to_chat(get_user(update.message.from_user.id), update.message.chat_id) 
#////////////////////////////
def depositar(bot, update):
	auser = update.message.from_user.username
	if auser is "":
		update.message.reply_text("Por Favor Insira um nickname na configuraçao do telegram!")
		return
	else:

		update.message.reply_text(
			"Seu Endereço de Deposito é %s" %
			get_address(get_user(update.message.from_user.id)))

		add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)

def sacar(bot, update):
	auser = update.message.from_user.username
	if auser is "":
		update.message.reply_text("Por Favor Insira um nickname na configuraçao do telegram!")
		return
	else:

		bal = get_balance(get_user(update.message.from_user.id))

		args = update.message.text.split()[1:]

	if len(args) == 2:
		try:
			amount = Decimal(args[1])
		except decimal.InvalidOperation:
			update.message.reply_text("Uso: /sacar <address> <valor>")
			return
		if bal - amount >= 0.1 and amount > 1.2:
			if validate_address(args[0]):
				rpc = AuthServiceProxy("http://%s:%s@%s:%d" %
									   (config['rpc']['user'],
										config['rpc']['password'],
										config['rpc']['host'],
										config['rpc']['port']))

				rpc.settxfee(0.1)
				txid = rpc.sendtoaddress(args[0], amount-1)
				give_balance(get_user(update.message.from_user.id), -amount)
				update.message.reply_text(
					"Saque De %f DASHP TX: %s" %
					(amount-1, "https://explorer.dashplatinum.org/tx/" + txid))
			else:
				update.message.reply_text("Carteira Invalida")
		else:
			update.message.reply_text("Saldo Insuficiente! Seu Saldo Restante deve ser maior que 0.1, A Taxa de saque é de 1 DASHP," +
									  " O Valor Minimo Para Saque é de 1.3 DASHP")
	else:
		update.message.reply_text("Uso: /sacar <address> <valor>")

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)


def converter(bot, update):
	args = update.message.text.split()[1:]

	if len(args) == 3:
		try:
			amount = Decimal(args[0])
		except decimal.InvalidOperation:
			update.message.reply_text("Uso: /converter <amount> <from> <to>")
			return

		request = requests.get('https://api.cryptonator.com/api/ticker/%s-%s' %
							   (args[1], args[2]))

		ticker = request.json()

		if ticker['success']:
			res = Decimal(ticker['ticker']['price']) * amount
			base = ticker['ticker']['base']
			target = ticker['ticker']['target']
			update.message.reply_text("%f %s = %f %s" % (amount, base, res,
									  target))
		else:
			update.message.reply_text("Error: %s " % ticker['error'])

	else:
		update.message.reply_text("Uso: /convert <amount> <from> <to>")

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)


def market(bot, update):
	args = update.message.text.split()[1:]

	if len(args) > 0:
		base = args[0]
		if len(args) > 1:
			target = args[1]
		else:
			target = 'usd'
	else:
		base = 'ok'
		target = 'btc'

	request = requests.get('https://api.cryptonator.com/api/full/%s-%s' %
						   (base, target))

	ticker = request.json()

	if ticker['success']:
		price = Decimal(ticker['ticker']['price'])
		volume = ticker['ticker']['volume']
		#change = ticker['ticker']['change']
		markets = ticker['ticker']['markets']

		message = "Price: %s Volume: %s Change: %s\n" % (price, volume, change)

		for market in markets:
			name = market['market']
			price = market['price']
			volume = market['volume']
			message += "\n%s - Price: %s Volume: %s" % (name, price, volume)

		update.message.reply_text(message)
	else:
		update.message.reply_text("Error: %s " % ticker['error'])

	add_to_chat(get_user(update.message.from_user.id), update.message.chat_id)

def valor(bot,update):
        edcashCapJson = requests.get('https://api.coingecko.com/api/v3/coins/dash-platinum').json()
        mk_cap = edcashCapJson ['market_data']['market_cap']['brl']
        pricebrl = edcashCapJson ['market_data']['current_price']['brl']
        priceusd = edcashCapJson ['market_data']['current_price']['usd']
        pricebtc = edcashCapJson ['market_data']['current_price']['btc']
        priceeth = edcashCapJson ['market_data']['current_price']['eth']
        update.message.reply_text("💵 Price: \n Cotação/Price: Coingeock \n DASHP Market Cap: R$:{:.8f}".format(mk_cap)+
"\n Price(BRL):  R${:.8f}".format(pricebrl) + "\n Price(USD):  ${:.8f}".format(priceusd) + "\n Price(BTC):  {:.8f}".format(pricebtc) + "\n Price(ETH):  {:.8f}".format(priceeth))

if __name__ == "__main__":
	updater = Updater("token")
	updater.dispatcher.add_handler(CommandHandler('start', start))
	updater.dispatcher.add_handler(CommandHandler('enviar', enviar))
	updater.dispatcher.add_handler(CommandHandler('registrar', registrar))
	updater.dispatcher.add_handler(CommandHandler('register', registrar))
	updater.dispatcher.add_handler(CommandHandler('saldo', saldo))
	updater.dispatcher.add_handler(CommandHandler('balance', saldo))
	updater.dispatcher.add_handler(CommandHandler('depositar', depositar))
	updater.dispatcher.add_handler(CommandHandler('deposit', depositar))
	updater.dispatcher.add_handler(CommandHandler('sacar', sacar))
	updater.dispatcher.add_handler(CommandHandler('witdhaw', sacar))
	updater.dispatcher.add_handler(CommandHandler('converter', converter))
	updater.dispatcher.add_handler(CommandHandler('ajuda', ajuda))
	updater.dispatcher.add_handler(CommandHandler('relp', ajuda))
	updater.dispatcher.add_handler(CommandHandler('distribuir', distribuir))
	updater.dispatcher.add_handler(CommandHandler('rain', distribuir))
	updater.dispatcher.add_handler(CommandHandler('info', info))
	updater.dispatcher.add_handler(CommandHandler('valor', valor))
	updater.dispatcher.add_handler(CommandHandler('price', valor))
	updater.dispatcher.add_handler(CommandHandler('regras', regras))
	updater.start_polling()
	updater.idle()
