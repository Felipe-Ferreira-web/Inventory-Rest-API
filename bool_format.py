from werkzeug.exceptions import BadRequest

def str_to_bool(value):
    """ Converte uma string ou booleano em um valor booleano.

        Parâmetros:
            value (str | bool): Valor a ser convertido. Pode ser uma string ('true', 'false', '1', '0') ou um booleano True/False.
    
        Retorna:
            bool: O valor booleano correspondente.
    
        Levanta:
            BadRequest: Se o valor não for um booleano ou uma string válida para conversão."""
    
    if isinstance(value, bool):
        return value
     
    if isinstance(value, str):

        if value.lower() in ['true', '1']:
            return True
        
        elif value.lower() in ['false', '0']:
            return False
        
    raise BadRequest("The value must be 'true', 'false', '1' or '0'.")