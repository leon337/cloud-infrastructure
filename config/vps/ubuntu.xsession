#!/bin/sh
unset DBUS_SESSION_BUS_ADDRESS
export XDG_CONFIG_DIRS=/etc/xdg
exec dbus-run-session -- xfce4-session
