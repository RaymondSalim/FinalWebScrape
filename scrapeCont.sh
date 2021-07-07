python main.py continue -r csv -ep 0 -sp 0 -f "$(find ./Output/ -maxdepth 1 -regextype sed -regex '.*/.*[csv]$')"
