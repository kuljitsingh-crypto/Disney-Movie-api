from flaskserver import server

if __name__=="__main__":
	server.run(host='0.0.0.0',port="5000",threaded=True,debug=True)