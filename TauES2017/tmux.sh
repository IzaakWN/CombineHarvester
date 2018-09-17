#alias sS='source ~/setup_Scripts/setup_SFrame.sh'
#alias cdB='cd ~/analysis/SFrameAnalysis/BatchSubmission' 

tmux new session \;\
  split-window -v \;\
  send-keys 'sC; cd TauES2017; echo "./doFit_TES.sh -t _mtlt50"' C-m \;\
  split-window -h \;\
  send-keys 'sC; cd TauES2017; echo "./doFit_TES.sh -t _ZTTregion"' C-m \;\
  select-pane -t 1 \;\

