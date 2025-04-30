ICCF ?= .
clean:
	rm -f ~/*.pgn $(ICCF)/*.pgn

$(ICCF)/events.pgn:
	cd $(ICCF) && awk 'FNR==1 && NR!=1 {print ""}{print}' ~/*.pgn > events.pgn

pgn: $(ICCF)/events.pgn

o:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @only.txt events.pgn

a:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @args.txt events.pgn

$(ICCF)/logrotate.conf:
	cd $(ICCF) && envsubst < logrotate.conf.tmpl > logrotate.conf

rotate: $(ICCF)/logrotate.conf
	cd $(ICCF) && logrotate -s ./logrotate.status ./logrotate.conf
