source ${HOME}/util/git/settings.sh

export PS1="\\u@\h \[\e[36m\]\\W\[\e[m\]\$(git_branch 1 ' ')\\$ \[\e]2;\$(git_branch 0 '' ' ')\\W \h\a\]"
