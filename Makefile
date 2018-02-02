SHELL := /bin/bash
PREFIX := crypto-escrow-sandbox
INSECURE ?= --insecure
KEY := $(PREFIX).$(SERVER_NAME)
NETRC := $(HOME)/.netrc
SAMPLE := $(shell echo "$$(<sample_transaction.json)")
export  # `export SERVER_NAME=example.com` in shell before `make deploy`
default: test2 test3
test2:
	echo test | python2 paypal_ipn.py
test3:
	echo test | python3 paypal_ipn.py
env set:
	$@
deploy: paypal_ipn.py
	scp paypal_ipn.py \
	 $(SERVER_NAME):/var/www/$(SERVER_NAME)/tmp/$(<:.py=.cgi)
remote: paypal_ipn.py deploy
	# to check certificates, `make INSECURE= remote`
	curl $(INSECURE) --data foo=bar https://$(SERVER_NAME)/tmp/$(<:.py=.cgi)
# the following rules require an entry, all on one line, in $HOME/.netrc
# machine crypto-escrow-sandbox.example.com
#  login APPID password APPKEY account TOKEN
# where APPID and APPKEY are given to you when you create a PayPal app,
# and TOKEN is given to you when you `make sandboxtoken`
# (you can leave that last part blank in .netrc until you have done so)
sandboxtoken:
	client_id=$$(awk '$$2 ~ /^$(KEY)$$/ {print $$4}' $(NETRC)) && \
	secret=$$(awk '$$2 ~ /^$(KEY)$$/ {print $$6}' $(NETRC)) && \
	curl --verbose https://api.sandbox.paypal.com/v1/oauth2/token \
	 --header "Accept: application/json" \
	 --header "Accept-Language: en_US" \
	 --user "$$client_id:$$secret" \
	 --data "grant_type=client_credentials"
payment:
	token=$$(awk '$$2 ~ /^$(KEY)$$/ {print $$8}' $(NETRC)) && \
	curl --verbose https://api.sandbox.paypal.com/v1/payments/payment \
	 --header "Content-Type: application/json" \
	 --header "Authorization: Bearer $$token" \
	 --data '$(SAMPLE)'
