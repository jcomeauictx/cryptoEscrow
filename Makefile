INSECURE ?= --insecure
export  # must first `export SERVER=example.com` in shell before `make deploy`
default: test2 test3
test2:
	echo test | python2 paypal_ipn.py
test3:
	echo test | python3 paypal_ipn.py
deploy: paypal_ipn.py
	scp paypal_ipn.py $(SERVER):/var/www/$(SERVER)/tmp/$(<:.py=.cgi)
remote: paypal_ipn.py deploy
	# to check certificates, `make INSECURE= remote`
	curl $(INSECURE) --data foo=bar https://$(SERVER)/tmp/$(<:.py=.cgi)
