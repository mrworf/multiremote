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

* IR-2-REST Gateway - REST interface allowing access to USB IR Toy v2
* ir-devices - Holds the IR codes to use with IR-2-REST
* Yamaha-2-REST Gateway - REST interface allowing access to Yamaha receivers with serial interface
* multiREMOTE UX - The HTML5/jQuery/Socket.IO based UX

All above mentioned projects can be found at https://github.com/mrworf

## Currently supported device

* Yamaha RX-V1900 via Yamaha-2-REST
* Plex Home Theater via built-in driver
* Roku via built-in driver
* Any IR device which can be taught to IR-2-REST
