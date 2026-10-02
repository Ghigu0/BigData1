ATTENZIONE 
        Nel progetto sarebbe presente anche la cartella "porto" che dentro ha il file csv. 
        Se la carichiamo su github rompiamo tutto e dobbiamo modificare lo storico dei commit ( un casino, mi è successo in passato). 
        Quindi ho aggiunto al gitignore la cartella /porto. Di conseguenza non cè nel github ma te la devi scaricare da Canvas.

Dati per connettersi alla Vm con il nostro profilo tramite la classe python del prof o manualmente

        HOST = "tdt4225-25.idi.ntnu.no"
        DATABASE = "gruppo_25"
        USER = "gruppo25"
        PASSWORD = "gruppo25"

per connettersi manualmente ( dopo aver acceso la VPN )

        ssh nomeutente@tdt4225-25.idi.ntnu.no 
        ssh francbin@tdt4225-25.idi.ntnu.no   
        
il mio nomeutente per esempio è francbin, è quello della mail istituzionale.

ho dovuto anche modificare il file requiriment.txt aggiornando la versione del connector con 26.7.0
