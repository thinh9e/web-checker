@echo off

call sass --no-source-map --style=compressed --watch main.scss ../static/css/style.css
