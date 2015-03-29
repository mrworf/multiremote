# multiRemote

Ever been in a part of your house were the remote doesn't reach? Ever had situations
where there are two people using parts of the same home entertainment system?

multiRemote aims to resolve these and more. It's the core of a solution which allows
for easy management of your A/V setup, using a web browser as the UI and UX for controlling
the system.

## Features

* REST api
* UI/UX separated from logic
* Conflict resolution (two users, two zones, one DVD player)
* Easy setup
* Subzoning, allowing one room/zone to have multiple displays
* Expandable in an unprecedented way compared to previous systems like Logitech Harmony, URC, etc.
* Cheap (hey, open source, can't get much cheaper)

## Related projects

* ircontroller - A small REST-2-IR gateway using USB IR Toy v2
* ir-devices - Holds the IR codes to use with ircontroller
* yamahacontroller - REST-2-RS232 gateway to talk to Yamaha receivers with serial interface
* multiRemoteWeb - The HTML5/jQuery/Socket.IO based UX (not yet released)

## Currently supported device

* Yamaha RX-V1900 via yamahacontroller
* Plex Home Theater via built-in driver
* Roku via built-in driver
* Any IR device which can be taught to ircontroller
