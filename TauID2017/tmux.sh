#alias sS='source ~/setup_Scripts/setup_SFrame.sh'
#alias cdB='cd ~/analysis/SFrameAnalysis/BatchSubmission' 

tmux new session \;\
  split-window -v \;\
  send-keys 'sC; cd TauID2017; echo "./doFit_TID.sh -c 2"' C-m \;\
  split-window -h \;\
  send-keys 'sC; cd TauID2017; echo "./doFit_TID.sh -c 3"' C-m \;\
  select-pane -t 1 \;\

