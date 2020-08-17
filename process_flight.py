
from Flights import complete_flight
from Flights import mini_bos_flight
from Flights import get_completed_flights
from Flights import get_completed_flights_avl_only
from Flights import get_completed_flights_rtp_only
from Flights import mark_bos_pulled

from Reports import generate_mini_bos_flight_sheets
from Reports import bos_flight_sheets
from Reports import bos_placemats
from Reports import bos_round_cup_labels

if __name__ == '__main__':

    option = ''

    while option != 'q':


        print(
            ('\n\n1: Enter Mini-BOS Entry IDs'
                '\n2: Process Mini-BOS Flight Sheets'
                '\n3: Enter Flight Places'
                '\n4: Mark BOS Entry as Pulled'
                '\n5: Show Completed Flights AVL Only'
                '\n6: Show Completed Flights RTP Only'
                '\n7: Show Completed Flights'
                '\n8: Generate BOS Flight Sheets, Cup Labels and Placemats'
                '\nq: Quit'
                '\n'
            )
        )

        try:
            option = input('Enter option: ')
        except Exception as e:
            option = ''

        option = option.lower()

        if option == '1':
            mini_bos_flight()
        elif option == '2':
                try:
                    choice = input('Enter flight number to process: ')
                except Exception as e:
                    choice = ''
                try:
                    choice = int(choice)
                except:
                    choice = ''

                if choice:
                    generate_mini_bos_flight_sheets(choice)

        elif option == '3':
            complete_flight()
        elif option == '4':
            mark_bos_pulled()        
        elif option == '5':
            get_completed_flights_avl_only()
        elif option == '6':
            get_completed_flights_rtp_only()
        elif option == '7':
            get_completed_flights()
        elif option == '8':
            bos_flight_sheets(descriptions=False)
            bos_flight_sheets()
            bos_round_cup_labels()
            bos_placemats()

