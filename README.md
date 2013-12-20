## Funksteckdosen 433Mhz mit iOS, Andoid App.  ##

Proect started by mario
[http://www.forum-raspberrypi.de/Thread-tutorial-funksteckdosen-433mhz-mit-ios-andoid-app](http://www.forum-raspberrypi.de/Thread-tutorial-funksteckdosen-433mhz-mit-ios-andoid-app)

----------


Zur Verwirklichung benötigst du folgendes: 
- Funksteckdosen der Marke Elro auch im Baumarkt erhältlich (z.B. Toom)
- Sendemodul 433Mhz auch andere müssten gehen, ich nutze dieses.
- Raspberry Pi mit Netzwerkverbindung
- Betriebssystem Wheezy (Tuts zur Installation gibt es mehr als genug!)
  Wichtig dabei ist, dass der SSH Zugang eingerichtet wurde. 
- Jumperkabel (F/F) oder andere Kabel und selber befestigen, aber Vorsicht!!
- Die App NetIO (Unter iOS ca. 7€)

1. Verkabelung
Sender                Raspberry Pi
ANT*
GND                   GND
DATA                  #17
VCC                    5V
                         -> Welchen Pin benötigt wird, 
                             bitte selber nachgucken. 

*= Abhängig vom Sendemodul benötigst du eine Antenne, oder halt keine, das sieht man daran, ob der Sender drei oder vier Stecker hat. Falls eine Art Spule schon auf dem Sende befestigt ist, fungiert diese als Antenne, sonst selber ein Kabel anbringen (Länge 17cm).

![](http://img3.fotos-hochladen.net/uploads/uerbersichtq6o0iyzk8f.jpg)

2. Vorbereitung zum Ansteuern via SSH
Du kannst die Codestücke aus dem jeweiligen Fenster gerne kopieren, jedoch Zeile für Zeile!
Als erstes benötigst du schon mal Wheezy auf einer SD Karte mit min. 2GB Speicherkapazität. 
Verbinde dich dann via SSH mit deinem Pi. 
z.B: Im Terminal unter MacOS so:

    ssh 192.168.xxx.xxx -l pi

Dann erst mal eine Aktualisierung der Paketquellen:

    sudo apt-get update
    
Nun bin ich über das Raspberry-Remote von xkonni gestolpert. Danke!
Installieren geht folgender maßen:
Als erstes benötigen wir das WiringPi von Godon:


    sudo apt-get install git-core
    git clone git://git.drogon.net/wiringPi
    cd wiringPi
    ./build
Nun hab ich das Projekt von xkonni “installiert”:

    cd ~
    git clone git://github.com/xkonni/raspberry-remote.git
    cd raspberry-remote
    
Als nächstes die send.cpp compilieren: 
Code: Alles markieren
make send

3. Ein erster Sendebefehl
Jetzt musst du zuerst deine Steckdosen konfigurieren:
Auf der Rückseite findest du oberhalb eine Möglichkeit die Dip-Schalter zu betätigen (hinter eine Klappe, Schraube lösen!).
Voreingestellt sind diese auf 11111 10000 für Steckdose A. 11111 01000 für B usw. 
Dabei stehen die ersten 5 Belegungen für den Hauscode. Dieser ist ebenfalls in der Fernbedienung eingestellt. Ich empfehle allerdings diesen zu ändern, damit nicht aus Versehen ein Nachbar eure Dosen steuert und du einen Softwarefehler befürchtest. Icon_wink

So jetzt der erste Test: 
Wichtig dabei ist, das du noch in dem Ordner raspberry-remote bist, da dort die send.spp liegt. Das erkennst du daran, das vor jedem SSH Befehl den du eingeben kannst steht pi@raspberrypi ~ §. Aber wenn du in einem Ordner bist steht da pi@raspberrypi ~/Ordnername $. Also hier: pi@raspberrypi ~/RPi.GPIO-0.1.0 $
Falls das nicht dort steht, musst du mit cd raspberry-remote in diesen Ordner gehen! 
Wie bereits gesagt gibt es einen Hauscode und eine Steckdosennummer. Gesendet wird:
sudo ./send <Hauscode> <Steckdosennummer> <Zustand 1 AN, 0 AUS>
Also im Auslieferungszustand mit Steckdose A für AN:


    sudo ./send 11111 1 1


Das macht Spaß Icon_smile Icon_biggrin2


4. Vorbereitung für die App: NetIO
Als erstes die App downloaden. 
Dann online registrieren unter: Oben rechts
So. 
Jetzt Benötigst du ein Python Skript, welches die Signale der App weiterleitet zu SSH Befehlen zum einfach Senden. 
Als erstes gehe in den homeordner des Pi's, falls du es nicht eh schon bist:

    cd

Dann installiere RPi.GPIO:

    wget http://pypi.python.org/packages/source/R/RPi.GPIO/RPi.GPIO-0.1.0.tar.gz
    tar zxf RPi.GPIO-0.1.0.tar.gz
    cd RPi.GPIO-0.1.0
    sudo python setup.py install

Jetzt bist du noch im Ordner RPi.GPIO-0.1.0




    sudo python netio_server.py
    
Falls du möchtest, das dieses Skript im Hintergrund läuft schreibe ein & dort hinter: 


    sudo python netio_server.py &

Jetzt kannst du das Terminal-Fenster schließen und ggf. deinen PC/Mac ausschalten...


5. App mit Oberfläche füllen
Auf dieser Seite kann nach dem Login eine App "erstellt" werden. 
Dazu einfach oben auf "Open-Config" -> "Empty" klicken. 
Jetzt hast du eine "Leere" Oberfläche. 
Als erstes musst du links unten bei Host und Port deine Daten eintragen. Also die IP deines Raspberrys und den Port den du im Skript eingestellt hast, bzw. so gelassen dann 54321. 
Unter "Add Item" -> "Button" kannst du einen neuen Button einfügen. Füge zum Test als erstes zwei Stück ein. Wenn du diese anklickst, kannst du links in der Leiste die Eigenschaften ändern. Test, Forum, Befehle usw. 
Also benenne Sie mit AN und AUS und füge bei beiden Buttons ein Send Attribute hinzu. 
In diesem Sendefeld schreibst du bei 
Button AN: 11111 1 1 -r 3  und bei 
Button AUS: 11111 1 0 -r 3 ein.
Das -r 3 steht für Sendewiederholungen. Also, falls das beim ersten mal nicht an der Steckdose ankommt, kannst du dir bei zwei, drei, vier mal senden sicher sein, das es die Steckdose erreicht. 

Klicke dann oben auf Save Online. 


6. In der App
Öffne die App auf deinem Smartphone, Tablett. 
Schüttle dein Gerät, damit sich ein kleines Fenster öffnet. (Alternativ mit zwei fingern von unten nach oben ziehen). 
Gib deine Logindaten ein und klicke Sync. 
Dann erscheint unterhalb der Logindaten ein neuer Eintrag namens New Configuration. Oder Unter einem anderen Namen, falls du Ihn geändert hast. 
Klicke drauf. 
Es öffnet sich die eingestellte Oberfläche! 