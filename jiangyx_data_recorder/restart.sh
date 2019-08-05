ps -efww|grep -w "ctrl_data_recorder.py"|grep -v grep|cut -c 9-15|xargs kill -9
nohup /usr/bin/python3 ./ctrl_data_recorder.py&




