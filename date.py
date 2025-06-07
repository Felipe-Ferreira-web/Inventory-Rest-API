from datetime import datetime

class Time(datetime):
    """ Classe que estende datetime para operações relacionadas a tempo formatado. """

    @staticmethod
    def register_time():
        """ Retorna o timestamp atual formatado como string no formato 'dd/mm/yyyy HH:MM:SS'.

            Retorna:
                str: Data e hora atual formatadas, por exemplo, '07/06/2025 14:30:25'. """
        
        time = datetime.now()
        time_format = time.strftime("%d/%m/%Y %H:%M:%S")
        time_format = str(time_format)
        return time_format