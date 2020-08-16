
from Flights import complete_flight
from Flights import mini_bos_flight
from Reports import generate_mini_bos_flight_sheets

if __name__ == '__main__':

    option = ''

    while option != 'q':


        print(
            ('\n\n1: Enter Mini-BOS Entry IDs'
                '\n2: Process Mini-BOS Flight Sheets'
                '\n3: Enter Flight Places'
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
        

